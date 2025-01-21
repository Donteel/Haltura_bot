import logging
from aiogram import Bot
from aiogram.exceptions import TelegramMigrateToChat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import ChatMemberAdministrator, InlineKeyboardMarkup, InlineKeyboardButton

from Utils.bot_instance import bot
from Utils.config import storage, main_chat



# async def get_admins(chat_id: int) -> list[tuple[str, str]]:
#     try:
#         admins = await bot.get_chat_administrators(chat_id)
#     except TelegramMigrateToChat as e:
#         # Получаем новый chat_id через migrate_to_chat_id
#         new_chat_id = e.migrate_to_chat_id
#         admins = await bot.get_chat_administrators(new_chat_id)
#         print(f"Admins moved to new chat: {admins}")
#
#     admin_list = []
#
#     for admin in admins:
#         if isinstance(admin, ChatMemberAdministrator):  # Проверяем, является ли участник администратором
#             username = admin.user.username if admin.user.username else "Donteel"
#             custom_title = admin.custom_title if admin.custom_title else "Администратор"
#             admin_info = (username, custom_title)  # username и статус администратора
#             admin_list.append(admin_info)
#
#     return admin_list

async def get_admins(chat_id: int) -> list[tuple[str, str]]:
    pass


async def state_for_user(user_id: int, chat_id: int) -> FSMContext:
    # Создаём контекст для определённого пользователя
    key = StorageKey(chat_id=chat_id,user_id=user_id,bot_id=7926311537)
    context = FSMContext(storage=storage, key=key)
    return context


# функция для публикации сообщения с привлечением HR
async def MessageForHr():
    try:
        await bot.send_message(
            text='<b>💼 Ищете сотрудников?</b>\n'
                    'Вы можете опубликовать свою вакансию абсолютно'
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