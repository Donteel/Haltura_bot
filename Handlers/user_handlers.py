import asyncio
import logging
from datetime import datetime, timedelta
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message,ReplyKeyboardRemove
from aiogram import F
from DataBase.MessageObject import MessageObject
from DataBase.postObject import PostObject
from MiddleWares.BlackListMiddleWares import CheckBlackListMiddleWare
from MiddleWares.PendingConfirmaionMiddleWares import CheckPendingConfirmMiddleware
from MiddleWares.SpamProtections import SpamProtected
from Utils.Keyboards import *
from aiogram import Router
from aiogram.filters import Command
from Utils.bot_instance import bot
from Utils.config import scheduler, r, orm_posts, orm_messages
from Utils.ScheduleTasks import time_zone
from Utils.StateModel import NewPost, DeactivatePostState
from Utils.config import action_orm, main_chat
from aiogram.fsm.context import FSMContext
from Utils.other import request_sender, post_moderation, post_publication, admin_broadcast


user_router = Router()
user_router.message.middleware(SpamProtected(rate_limit=1))
user_router.message.middleware(CheckPendingConfirmMiddleware())
user_router.message.middleware(CheckBlackListMiddleWare())
user_router.callback_query.middleware(CheckBlackListMiddleWare())

# @user_router.message()
# async def start(message):
#     print(message.chat.id)

@user_router.message(Command('start'))
async def start(message: Message):

    if await action_orm.create_user(
            tg_id=message.from_user.id,
            username=message.from_user.username):
        logging.info('Пользователь добавлен в базу')
    else:
        logging.info('Пользователь уже есть в базе')

    await message.answer('Добро пожаловать в Халтура бот,выбери действие.'
                        ,reply_markup=btn_home())


@user_router.message(F.text == '❌ Отменить')
async def start(message: Message,state: FSMContext):
    await state.clear()
    await message.answer('Действие отменено',reply_markup=btn_home())


@user_router.message(Command('help'))
async def start(message: Message):
    await message.reply('Можешь связаться с нужным тебе администратором',
                        reply_markup=btn_links(links=await action_orm.get_admins())
                        )


@user_router.message(F.text == '📢 Опубликовать готовый пост')
async def create_post(message: Message,state:FSMContext):

    await message.answer('<b>Отправь готовый пост в формате <u>текста!</u></b>\n'
                         'Оформив вакансию по правилам ее одобрят быстрее.',
                         reply_markup=btn_cancel())

    await state.update_data(username=message.from_user.username)

    await state.set_state(NewPost.awaiting_finished_post)
    logging.info(f'Пользователь {message.from_user.id} активировал кнопку публикации готового поста')


@user_router.message(F.text == '❌ Закрыть пост')
async def create_post(message: Message,state:FSMContext):

    await message.answer('Введите ID сообщение полученное при публикации',reply_markup=btn_cancel())
    await state.set_state(DeactivatePostState.waiting_post_id)


# обработчик закрытия поста
@user_router.message(DeactivatePostState.waiting_post_id, F.text)
async def deactivate_post(message: Message,state:FSMContext):
    try:
        post_id = int(message.text)
    except ValueError:
        await message.answer('Нужно отправить номер сообщения без букв,пробелов и любых знаков!')
        return
    else:

        if post_data:= await orm_posts.get_post(post_id=post_id,
                                                user_id=message.chat.id):

            try:
                await message.bot.edit_message_text(text=f"{post_data.post_text}\n ВАКАНСИЯ ЗАКРЫТА❌",
                                                    chat_id=int(main_chat),
                                                    message_id=int(post_data.post_id)
                                                    )
                await orm_posts.post_deactivate(
                    user_id=int(message.from_user.id),
                    post_id=int(post_data.post_id
                        )
                )
                await message.answer('Сообщение успешно деактивировано',
                                     reply_markup=btn_home()
                                     )
                await state.clear()

            except TelegramBadRequest:
                await message.answer('Сообщение уже деактивировано ранее',reply_markup=btn_home())
                await state.clear()

        else:
            await message.answer('Пост с таким номером не был найден',reply_markup=btn_cancel())


# обработчик не текстовых постов
@user_router.message(~F.text,NewPost.awaiting_finished_post)
async def awaiting_post(message: Message):

    await message.answer('К сожалению по формату группы,мы публикуем только текстовые вакансии.\n'
                         'Повтори отправку вакансии используя текст и эмодзи по желанию.',
                         reply_markup=btn_cancel()
                         )


# обработка готовой вакансии от пользователя
@user_router.message(F.text,NewPost.awaiting_finished_post)
async def awaiting_post(message: Message,state:FSMContext):
    await message.answer('Сейчас я проверю твою вакансию...')

    username = message.from_user.username or "Неизвестно"
    admin_data = await action_orm.get_admins_id()
    user_data = await state.get_data()
    post_text = user_data.get('post_text',message.text)

    if await post_moderation(post_text):

        # создать  запись в бд
        post_id = await orm_posts.create_new_post(user_id=message.chat.id,
                                                   username=username,
                                                   post_text=post_text
                                                   )

        # Добавляем задачу на публикацию нового поста в канал
        task_data = scheduler.add_job(
            func=post_publication,
            trigger="date",
            args=[main_chat,post_id],
            run_date = datetime.now(time_zone) + timedelta(minutes=5)
        )

        # добавляем job_id к записи
        await orm_posts.addJobId_to_post(post_id,task_data.id)

        # уведомить пользователя
        await message.answer('Публикация прошла автоматическую проверку и будет опубликована через 5 минут.'
                             'Спасибо за использование сервиса!',reply_markup=btn_home())


        # уведомить администраторов
        await request_sender(admin_data= await action_orm.get_admins_id(),
                             post_id=post_id)

        # удалить временные данные
        await state.clear()

    else:
        # добавить вакансию во временную базу данных
        post_id = await orm_posts.create_new_post(user_id=message.chat.id,
                                                   username=username,
                                                   post_text=post_text,
                                                   )

        # отправить вакансию на одобрение администраторам
        for admin in admin_data:
            ms_obj = await bot.send_message(text=
                                   "Вакансия требует ручной проверки!\n\n"
                                   f"Отправитель - @{username}\n"
                                   f"Текст вакансии:\n"
                                   f"{post_text}",
                                   chat_id=admin,
                                   reply_markup=btn_approval(post_id)
                                   )

            # сохранить messages администраторов
            admin_message = MessageObject(admin_id=admin,
                                          temp_id=post_id,
                                          message_id=ms_obj.message_id
                                          )

            await orm_messages.add_message_data(admin_message)

        # уведомить пользователя
        await message.answer("Вакансия не прошла автоматическую проверку.\n"
                             "Скоро администраторы проверят ее вручную",
                             reply_markup=btn_standby())

        await state.clear()
        await state.set_state(NewPost.pending_confirmation)


@user_router.message(Command("rules"))
@user_router.message(F.text == '📜 Правила')
async def rules(message: Message):
    await message.answer('Правила публикации постов!',
                         reply_markup=btn_rules(r'https://telegra.ph/Pravila-dlya-reklamodatelej-12-20')
                         )

