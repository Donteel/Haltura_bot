import logging
from aiogram import Bot
from aiogram.exceptions import TelegramMigrateToChat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import ChatMemberAdministrator, InlineKeyboardMarkup, InlineKeyboardButton

from Utils.Keyboards import btn_admin_confirm
from Utils.StateModel import AdminState
from Utils.bot_instance import bot
from Utils.config import storage, main_chat


async def state_for_user(user_id: int, chat_id: int) -> FSMContext:
    # Создаём контекст для определённого пользователя
    key = StorageKey(chat_id=chat_id,user_id=user_id,bot_id=7926311537)
    context = FSMContext(storage=storage, key=key)
    return context


async def clearing_of_all_states(id_data:list[int]):
    for object_id in id_data:
        local_state = await state_for_user(object_id,object_id)
        await local_state.clear()

# функция для публикации сообщения с привлечением HR
async def MessageForHr():
    try:
        await bot.send_message(
            text='<b>💼 Ищете сотрудников?</b>\n'
                    'Вы можете опубликовать свою вакансию'
                    ' бесплатно через нашего Telegram-бота! 🎯',
            chat_id=int(main_chat),
            reply_markup=
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Опубликовать 🔰',url='t.me/Haltura98_bot')]
            ]
            )
        )
    except Exception as e:
        logging.error(e)


async def request_sender(admin_data:list[int],post_text:str,username:str,post_id:int):

    """
    Функция для отправления заявки всем администраторам
    :param admin_data: ID администраторов
    :param post_text: текст заявки
    :param username: username отправителя
    :param post_id: ID поста
    :return: None
    """

    # отправка заявки администраторам
    for admin_id in admin_data:

        # создаем объект state для админа
        local_state = await state_for_user(admin_id, admin_id)
        # меняем его состояние в ожидания ответа на заявку
        await local_state.set_state(AdminState.waiting_action)

        # отправляем заявку администратору
        message_obj = await bot.send_message(
            chat_id=admin_id,
            text=f"{post_text}\n"
                 f"Отправитель - @{username}",
            reply_markup=btn_admin_confirm(post_id)
        )
        await local_state.update_data(message_id=message_obj.message_id)