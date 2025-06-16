import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from utils.config import action_orm


class AddUserMiddleware(BaseMiddleware):

    def __init__(self):
        pass

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: Message | CallbackQuery,
                       data: Dict[str, Any]
                       ):

        logging.info('Проверка регистрации пользователя.')

        if isinstance(event, Message):
            user_data = await action_orm.get_user(event.chat.id)
            if  not user_data:
                await action_orm.create_user(event.chat.id,
                                             event.from_user.username
                                             )



        elif isinstance(event, CallbackQuery):
            user_data = await action_orm.get_user(event.message.chat.id)
            if not user_data:
                await action_orm.create_user(event.message.chat.id, event.message.from_user.username)

        return await handler(event, data)