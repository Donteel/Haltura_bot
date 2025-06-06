from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PostObject(BaseModel):
    """
    Модель, представляющая публикацию пользователя.

    Используется для хранения и передачи информации о посте.

    Атрибуты:
        id (int | None): Уникальный идентификатор поста.
        user_id (int | None): ID пользователя, который создал пост.
        username (str | None): Имя пользователя.
        post_text (str | None): Содержимое публикации.
        post_id (int | None): ID связанного сообщения (неактуально для TempPost).
        status (bool | None): Статус публикации (например, опубликовано или нет).
        key (str | None): Уникальный ключ для идентификации поста.
        created_at (datetime | None): Дата и время создания поста.
    """

    id: Optional[int] = Field(default=None, description="Уникальный идентификатор поста")
    user_id: Optional[int] = Field(default=None, description="ID пользователя, создавшего пост")
    username: Optional[str] = Field(default=None, description="Имя пользователя")
    post_text: Optional[str] = Field(default=None, description="Содержимое публикации")
    message_id: Optional[int] = Field(default=None, description="ID связанного сообщения (не для TempPost)")
    temp_id: Optional[int] = Field(default=None, description="ID записи в бд (для TempPost)")
    status: Optional[str] = Field(default="pending", description="Статус публикации (pending,canceled,published)")
    job_id: Optional[str] = Field(default=None,description="id задачи на публикацию")
    created_at: Optional[datetime] = Field(default=None, description="Дата и время создания поста")




