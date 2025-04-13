import logging
from typing import Callable, Any, Dict, Awaitable
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram import BaseMiddleware
from Utils.StateModel import NewPost
from Utils.bot_instance import bot
from Utils.config import storage, action_orm
from Utils.other import state_for_user


class CheckBlackListMiddleWare(BaseMiddleware):

    def __init__(self):
        pass

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
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

