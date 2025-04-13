from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserObject(BaseModel):
    """
    Модель, представляющая пользователя.

    Используется для хранения информации о пользователях, взаимодействующих с системой (например, в Telegram-боте или веб-приложении).

    Атрибуты:
        id (int | None): Уникальный идентификатор записи в базе данных.
        username (str | None): Имя пользователя (например, Telegram username).
        user_id (int | None): Уникальный Telegram ID или внешний ID пользователя.
        created_at (datetime | None): Дата и время регистрации пользователя.
    """


    user_id: Optional[int] = Field(default=None, description="Telegram ID пользователя")
    username: Optional[str] = Field(default=None, description="Имя пользователя (username)")
    created_at: Optional[datetime] = Field(default=None, description="Дата и время регистрации")
