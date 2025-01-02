from aiogram import Bot
from aiogram.exceptions import TelegramMigrateToChat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import ChatMemberAdministrator

from Utils.config import storage


async def get_admins(chat_id: int, bot: Bot) -> list[tuple[str, str]]:
    try:
        admins = await bot.get_chat_administrators(chat_id)
    except TelegramMigrateToChat as e:
        # Получаем новый chat_id через migrate_to_chat_id
        new_chat_id = e.migrate_to_chat_id
        admins = await bot.get_chat_administrators(new_chat_id)
        print(f"Admins moved to new chat: {admins}")

    admin_list = []

    for admin in admins:
        if isinstance(admin, ChatMemberAdministrator):  # Проверяем, является ли участник администратором
            username = admin.user.username if admin.user.username else "No username"
            custom_title = admin.custom_title if admin.custom_title else "No title"
            admin_info = (username, custom_title)  # username и статус администратора
            admin_list.append(admin_info)

    return admin_list


async def state_for_user(user_id: int, chat_id: int) -> FSMContext:
    # Создаём контекст для определённого пользователя
    key = StorageKey(chat_id=chat_id,user_id=user_id,bot_id=7926311537)
    context = FSMContext(storage=storage, key=key)
    return context