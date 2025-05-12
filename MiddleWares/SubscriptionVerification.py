import logging
from typing import Callable, Any, Dict, Awaitable

from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram import BaseMiddleware

from Utils.Keyboards import btn_link, btn_subscribe
from Utils.config import main_chat
from Utils.bot_instance import bot
from Utils.other import check_member_status


class SubscriptionVerificationMiddleware(BaseMiddleware):
    def __init__(self):
        pass

    async def __call__(self,
                 handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                 event: TelegramObject | Message | CallbackQuery,
                 data: Dict[str, Any]
                 ):

        logging.info('Мидлварь для проверки подписки')
        if isinstance(event, Message):
            user_id = event.from_user.id
            try:
                if not await check_member_status(bot,
                                             group_id=main_chat,
                                             user_id=user_id):
                    await bot.send_message(text='Чтобы продолжить необходимо подписаться на нашу группу.',
                                           chat_id=user_id,
                                           reply_markup=btn_subscribe()
                                           )
                    return False
            except TelegramForbiddenError:
                logging.info('Бот не имеет доступа к группе')
                return False
        return await handler(event, data)