import logging
from datetime import datetime, timedelta
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message,ReplyKeyboardRemove
from aiogram import F
from MiddleWares.PendingConfirmaionMiddleWares import CheckPendingConfirmMiddleware
from MiddleWares.SpamProtections import SpamProtected
from Utils.Keyboards import *
from aiogram import Router
from aiogram.filters import Command
from Utils.ScheduleTasks import scheduler, time_zone
from Utils.StateModel import NewPost, DeletePostState
from Utils.config import action_orm, main_chat
from aiogram.fsm.context import FSMContext
from Utils.other import request_sender, post_moderation, admin_broadcast, job_posting

user_router = Router()
user_router.message.middleware(SpamProtected(rate_limit=1))
user_router.message.middleware(CheckPendingConfirmMiddleware())

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
                         'Оформив текст по правилам его одобрят быстрее.',
                         reply_markup=btn_cancel()
                         )

    await state.update_data(username=message.from_user.username)

    await state.set_state(NewPost.awaiting_finished_post)
    logging.info(f'Пользователь {message.from_user.id} активировал кнопку публикации готового поста')


@user_router.message(F.text == '❌ Закрыть пост')
async def create_post(message: Message,state:FSMContext):

    await message.answer('Введите ID сообщение полученное при публикации',reply_markup=btn_cancel())
    await state.set_state(DeletePostState.waiting_post_id)


@user_router.message(DeletePostState.waiting_post_id,F.text)
async def delete_post(message: Message,state:FSMContext):
    try:
        post_id = int(message.text)
    except ValueError:
        await message.answer('Нужно отправить номер сообщения без букв,пробелов и любых знаков!')
        return
    else:
        print(message.from_user.id)
        if post_data:= await action_orm.get_post(message_id=post_id,user_id=message.from_user.id):
            print(int(main_chat),int(post_data['message_id']))
            try:
                await message.bot.edit_message_text(text=f"{post_data['post_text']}\n ВАКАНСИЯ ЗАКРЫТА❌",
                                                    chat_id=int(main_chat),
                                                    message_id=int(post_data['message_id'])
                                                    )
                await action_orm.post_deactivate(
                    user_id=int(message.from_user.id),
                    message_id=int(post_data['message_id']
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

@user_router.message(~F.text,NewPost.awaiting_finished_post)
async def awaiting_post(message: Message):

    await message.answer('К сожалению по формату группы,мы не публикуем только текстовые вакансии.\n'
                         'Повтори отправку вакансии используя текст и эмодзи по желанию.',
                         reply_markup=btn_cancel()
                         )

@user_router.message(F.text,NewPost.awaiting_finished_post)
async def awaiting_post(message: Message,state:FSMContext):

    logging.info(f'Пользователь {message.from_user.id}  отправляет пост на проверку.')

    await message.answer("проверка вакансии, ожидайте...",reply_markup=ReplyKeyboardRemove())

    # Если username указан, то он будет отображаться, а если нет, то будет "Неизвестен"
    username = f"@{message.from_user.username}" if message.from_user.username else "Неизвестен"

    state_data = await state.get_data()

    # Создаем запись во временную базу данных

    post_text = state_data.get('post_text',message.text)

    logging.info(f'Пользователь {username} предложил новую вакансию.\n'
                 f'Текст сообщения -  {post_text}\n')


    # получаем ID всех администраторов
    admin_data:list[int] = await action_orm.get_admins_id()


    logging.info(f'Список администраторов - {admin_data}')

    if await post_moderation(post_text):
        await message.answer("Ваш пост прошел автоматическую проверку и будет опубликован.\n"
                             "После публикации вы получите уведомление, ожидайте...", reply_markup=btn_home()
                             )

        await admin_broadcast(admin_data, "Я получил новую вакансию от пользователя\n"
                                          "Она будет опубликована в течении 5 минут после получения этого сообщения\n"
                                          "Текст вакансии:\n"
                                          f"{post_text}\n"
                                          f"Отправитель {username}\n")

        scheduler.add_job(job_posting,
                          trigger='date',
                          run_date=datetime.now(time_zone) + timedelta(minutes=5),
                          args=(post_text, main_chat, message.chat.id)
                          )
    else:

        # создаем временную запись в базе данных
        post_id = await action_orm.create_temp_post(user_id=message.from_user.id,
                                                    post_text=post_text,
                                                    username=username
                                                    )

        logging.info(f'Вакансия добавлена в временную базу данных, ID записи - {post_id}')


        try:
            # рассылаем заявку всем администраторам
            await request_sender(admin_data=admin_data,
                                 post_text=post_text,
                                 username=message.from_user.username,
                                 post_id=post_id
                                 )

        except Exception as e:
            logging.error(f'Возникла ошибка при рассылке вакансии администраторам\n {e}')
            await message.answer("Возникла не предвиденная ошибка,мы скоро исправим ее.",reply_markup=btn_home())
            await state.clear()
        else:
            await message.answer("<b>Ваша вакансия не прошла автоматическую проверку.</b>\n"
                                 "Скоро мы проверим ее вручную,ожидайте уведомление.",
                                 reply_markup=btn_standby()
                                 )

            await state.set_state(NewPost.pending_confirmation)

@user_router.message(Command("rules"))
@user_router.message(F.text == '📜 Правила')
async def rules(message: Message):
    await message.answer('Правила публикации постов!',
                         reply_markup=btn_rules(r'https://telegra.ph/Pravila-dlya-reklamodatelej-12-20')
                         )

