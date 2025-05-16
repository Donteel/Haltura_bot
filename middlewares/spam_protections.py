import logging
import time
from typing import Callable, Any, Dict, Awaitable
from aiogram.types import TelegramObject, Message
from aiogram import BaseMiddleware


class SpamProtected(BaseMiddleware):
    def __init__(self,rate_limit: int = 2):
        """
            Инициализация middleware защиты от спама.
            :param rate_limit: Минимальное количество секунд между сообщениями от одного пользователя.
        """
        self.rate_limit = rate_limit
        self.last_message_time = {}

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        """
            Метод, вызываемый при обработке события.
            Проверяет, прошло ли достаточно времени с последнего сообщения пользователя.
        """
        if isinstance(event, Message):
            user_id = event.from_user.id
            current_time = time.time()

            # Проверяем, было ли сообщение от пользователя недавно
            if user_id in self.last_message_time:
                elapsed_time = current_time - self.last_message_time[user_id]
                if elapsed_time < self.rate_limit:
                    # Если сообщение отправлено слишком рано, игнорируем его
                    logging.info(f'Пользователь {event.from_user.username} спамит!')
                    return
            # обновляем время последнего сообщения
            self.last_message_time[user_id] = current_time
        return await handler(event, data)