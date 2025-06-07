from typing import Optional

from pydantic import BaseModel, Field


class MessageObject(BaseModel):

    admin_id: Optional[int] = Field(description='id администратора')
    user_id: Optional[int] = Field(default=None,description="id пользователя")
    post_id: Optional[int] = Field(description="временный id записи в бд")
    message_id: Optional[int] = Field(description='id сообщения связанный с конкретной записью в бд')
    message_text: Optional[str] = Field(default=None,description="текст сообщения")