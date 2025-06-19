import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from utils.config import action_orm


class CheckLimitMiddleware(BaseMiddleware):
    def __init__(self):
        pass

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: Message | CallbackQuery,
                       data: Dict[str, Any]
                       ):

        if isinstance(event, Message):

            user_limit = await action_orm.get_user_limit(user_id=event.chat.id)

            await action_orm.create_user_limit(event.chat.id,limit=2)

        return await handler(event, data)