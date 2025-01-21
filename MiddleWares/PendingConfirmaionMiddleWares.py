import logging
from typing import Callable, Any, Dict, Awaitable
from aiogram.types import TelegramObject, Message
from aiogram import BaseMiddleware
from Utils.StateModel import NewPost
from Utils.config import storage
from Utils.other import state_for_user


class CheckPendingConfirmMiddleware(BaseMiddleware):
    def __init__(self):
        pass

    async def __call__(self,
                 handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                 event: TelegramObject,
                 data: Dict[str, Any]
                 ):

        logging.info('Мидлвари для проверки состояния сработал')
        if isinstance(event, Message):

            user_id = event.from_user.id
            chat_id = event.chat.id

            context = await state_for_user(user_id, chat_id)
            user_state = await context.get_state()

            logging.info(f'Состояние пользователя {user_state}')

            if   user_state == NewPost.pending_confirmation:
                await event.answer('Дождись одобрения заявки!')
                return

        return await handler(event, data)