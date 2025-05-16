import logging
from typing import Callable, Any, Dict, Awaitable
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram import BaseMiddleware
from utils.config import action_orm


class CheckBlackListMiddleWare(BaseMiddleware):

    def __init__(self):
        pass

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: Message | CallbackQuery,
                       data: Dict[str, Any]
                       ):

        if isinstance(event, Message):
            user_data = await action_orm.get_user_from_blacklist(event.chat.id)
            if  not user_data:
                return await handler(event, data)


        elif isinstance(event, CallbackQuery):
            user_data = await action_orm.get_user_from_blacklist(event.message.chat.id)
            if not user_data:
                return await handler(event, data)

