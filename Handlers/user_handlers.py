import logging
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram import F

from MiddleWares.PendingConfirmaionMiddleWares import CheckPendingConfirmMiddleware
from MiddleWares.SpamProtections import SpamProtected
from Utils.Keyboards import *
from aiogram import Router
from aiogram.filters import Command
from Utils.StateModel import NewPost, DeletePostState
from Utils.config import action_orm, main_chat
from aiogram.fsm.context import FSMContext
from Utils.other import request_sender

user_router = Router()
user_router.message.middleware(SpamProtected(rate_limit=1))
user_router.message.middleware(CheckPendingConfirmMiddleware())

# @user_router.message()
# async def start(message):
#     print(message.chat.id)

@user_router.message(Command('start'))
async def start(message: Message,state: FSMContext):

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

    await message.answer('<b>Пришли мне готовый пост <u>только текстом!</u></b>\n'
                         'Не забудь указать контактные данные.',
                         reply_markup=btn_cancel())
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

@user_router.message(F.photo,NewPost.awaiting_finished_post)
async def awaiting_post(message: Message,state:FSMContext):

    await message.answer('К сожалению по формату группы,мы не публикуем заявку с фото или видео материалами.\n'
                         'Отправьте текст заявки или отмени действие.',
                         reply_markup=btn_cancel()
                         )



@user_router.message(F.text,NewPost.awaiting_finished_post)
async def awaiting_post(message: Message,state:FSMContext):
    logging.info(f'Пользователь {message.from_user.id}  отправляет пост на проверку.')
    # Создаем запись во временную базу данных
    post_text = message.text

    post_id = await action_orm.create_temp_post(user_id=message.from_user.id,
                                                post_text=post_text,
                                                username=message.from_user.username
                                                )

    logging.info(f'Пользователь {message.from_user.id} предложил новую вакансию.\n'
                 f'Текст сообщения -  {post_text}\n'
                 f'Вакансия добавлена в временную базу данных, ID записи - {post_id}'
                 )

    # получаем ID всех администраторов
    admin_data:list[int] = await action_orm.get_admins_id()

    logging.info(f'Список администраторов - {admin_data}')

    try:
        # рассылаем заявку всем администраторам
        await request_sender(admin_data=admin_data,
                             post_text=message.text,
                             username=message.from_user.username,
                             post_id=post_id
                             )
    except Exception as e:
        logging.error(f'Возникла ошибка при рассылке вакансии администраторам\n {e}')
    else:
        await message.answer('Ваш пост отправлен на проверку,ожидайте обновлений',
                             reply_markup=btn_standby()
                             )
        await state.set_state(NewPost.pending_confirmation)


@user_router.message(F.text == '📜 Правила')
async def start(message: Message):
    await message.answer('Правила публикации постов!',
                         reply_markup=btn_rules(r'https://telegra.ph/Pravila-dlya-reklamodatelej-12-20')
                         )

