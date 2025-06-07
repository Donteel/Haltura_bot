import asyncio
import logging
from datetime import datetime, timedelta
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram import F
from database.message_object import MessageObject
from middlewares.add_user_middleware import AddUserMiddleware
from middlewares.blacklist_middlewares import CheckBlackListMiddleWare
from middlewares.pending_confirmation_middlewares import CheckPendingConfirmMiddleware
from middlewares.spam_protections import SpamProtected
from middlewares.subscription_verification import SubscriptionVerificationMiddleware
from utils.keyboards import *
from aiogram import Router
from aiogram.filters import Command
from utils.bot_instance import bot
from utils.config import scheduler, orm_posts, orm_messages
from utils.schedule_tasks import time_zone
from utils.state_models import NewPost, DeactivatePostState
from utils.config import action_orm, main_chat
from aiogram.fsm.context import FSMContext
from utils.other import request_sender, post_moderation, post_publication, check_member_status

user_router = Router()


user_router.message.middleware(CheckBlackListMiddleWare())
user_router.callback_query.middleware(CheckBlackListMiddleWare())
user_router.message.middleware(AddUserMiddleware())
user_router.callback_query.middleware(AddUserMiddleware())
user_router.message.middleware(SpamProtected(rate_limit=1))
user_router.message.middleware(CheckPendingConfirmMiddleware())
user_router.message.middleware(SubscriptionVerificationMiddleware())
user_router.callback_query.middleware(SubscriptionVerificationMiddleware())

# @user_router.message()
# async def print_id(message):
#     print(message.forward_from_chat.id)

@user_router.message(Command('start'))
async def start(message: Message):


    await message.answer('Как вы хотите отправить вакансию?'
                        ,reply_markup=btn_home())


@user_router.message(F.text == '❌ Отменить')
async def cancel_func(message: Message,state: FSMContext):
    await state.clear()
    await message.answer('Действие отменено',reply_markup=btn_home())


@user_router.callback_query(F.data == 'subscribe')
async def subscribe(callback: CallbackQuery):
    logging.info('Активирована кнопка проверки подписки.')
    if await check_member_status(bot,
                                 user_id=callback.from_user.id,
                                 group_id=main_chat):
        await start(message=callback.message)
    else:
        await callback.answer(show_alert=True,text='Вы все еще не подписаны...')
    await callback.answer()



@user_router.message(Command('help'))
async def help_func(message: Message):
    await message.reply('Можешь связаться с нужным тебе администратором',
                        reply_markup=btn_admins(links=await action_orm.get_admins())
                        )


@user_router.message(F.text == '📤 Отправить готовую')
async def create_post(message: Message,state:FSMContext):

    await message.answer('<b>Отправь готовый пост в формате <u>текста!</u></b>\n'
                         'Оформив вакансию по правилам ее одобрят быстрее.',
                         reply_markup=btn_cancel())

    await state.update_data(username=message.from_user.username)

    await state.set_state(NewPost.awaiting_finished_post)
    logging.info(f'Пользователь {message.from_user.id} активировал кнопку публикации готового поста')


@user_router.message(F.text == '❌ Закрыть вакансию')
async def create_post(message: Message,state:FSMContext):

    await message.answer('Введите ID сообщение полученное при публикации',reply_markup=btn_cancel())
    await state.set_state(DeactivatePostState.waiting_post_id)


# обработчик закрытия поста
@user_router.message(DeactivatePostState.waiting_post_id, F.text)
async def deactivate_post(message: Message,state:FSMContext):
    try:
        # получаем post_id пользователя для удаления
        msg_id = int(message.text)
    except ValueError:
        await message.answer('Нужно отправить номер сообщения без букв,пробелов и любых знаков!')
        return
    else:

        # проверяем есть ли такой пост в базе данных
        if post_data:= await orm_posts.check_post_by_msg_id(message_id=msg_id,
                                                user_id=message.chat.id):

            try:
                # изменяем сообщение
                await message.bot.edit_message_text(
                    text=f"<s>{post_data.post_text}</s>\n\n"
                         f" [ВАКАНСИЯ ЗАКРЫТА❌]",
                    chat_id=int(main_chat),
                    message_id=int(post_data.message_id)
                )

                # меняем статус поста в базе данных
                await orm_posts.post_deactivate(
                    post_id=int(post_data.id)
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

    await message.answer('🤖 Вакансия проходит проверку...')

    username = message.from_user.username or "Неизвестно"
    admin_data = await action_orm.get_admins_id()
    user_data = await state.get_data()
    post_text = user_data.get('post_text',message.text)

    ai_verification = await post_moderation(post_text)

    # проверяет на положительный ответ
    if isinstance(ai_verification,int):

        # создать  запись в бд
        post_id = await orm_posts.create_new_post(user_id=message.chat.id,
                                                   username=username,
                                                   post_text=post_text
                                                   )

        logging.info(f'ID нового поста в BD {post_id}')

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
        await message.answer("<b>Всё в порядке!</b>\n"
                             "Вакансия будет опубликована через 5 минут.\n"
                             "Спасибо, что остаётесь нами!",
                             reply_markup=btn_home()
                             )


        # уведомить администраторов
        await request_sender(admin_data= await action_orm.get_admins_id(),
                             post_id=post_id)

        # удалить временные данные
        await state.clear()

    # проверяет на отрицательный ответ с причиной
    elif isinstance(ai_verification,list):

        ai_verdict = ai_verification[1]

        await message.answer(
            '<b>Ваша вакансия не прошла проверку</b>\n'
                 '<b>[Причина]</b>:\n\n'
                f'<i>{ai_verdict}</i>\n\n'
                f'Устраните проблемы и повторите отправку. '
                f'Eсли причина вам не ясна обратитесь к администратору по команде /help .',
                 reply_markup=btn_home()
        )

        for admin in admin_data:
            await bot.send_message(
                text=f"<b>[Я отменил вакансию]</b>\n"
                     f"<b>[Отправитель]</b> - @{username}\n"
                     f"<b>[Текст вакансии]:</b>\n\n"
                     f"<i>{post_text}</i>",
                chat_id=admin,
                reply_markup=ReplyKeyboardRemove()
            )

    # проверяет на False
    elif not ai_verification:
        # добавить вакансию базу данных
        post_id = await orm_posts.create_new_post(user_id=message.chat.id,
                                                  username=username,
                                                  post_text=post_text
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
        await message.answer("Система не смогла автоматически одобрить вакансию.\n"
                             " Я передал ее на проверку администратору.",
                             reply_markup=btn_standby())

        await state.clear()
        await state.set_state(NewPost.pending_confirmation)


@user_router.message(Command("rules"))
@user_router.message(F.text == '📜 Правила')
async def rules(message: Message):
    await message.answer('Правила публикации постов!',
                         reply_markup=btn_rules(r'https://telegra.ph/Pravila-dlya-reklamodatelej-12-20')
                         )