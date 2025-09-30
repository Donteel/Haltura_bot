import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, and_

from database.base_model import MessageModel
from database.objects.message_object import MessageObject
from database.session_config import with_session, AsyncSession, AsyncSessionLocal


class MessageManagementBase:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.session_factory = AsyncSessionLocal

    def __del__(self):
        self.__instance = None

    @with_session
    async def add_message_data(self,session: AsyncSession,ms_obj: MessageObject)-> bool:

        message_data = MessageModel(admin_id=ms_obj.admin_id,
                                    post_id=ms_obj.post_id,
                                    message_id=ms_obj.message_id)
        try:
            session.add(message_data)
            await session.commit()
            return True
        except IntegrityError as e:
            logging.error(e)
            await session.rollback()
            return False


    @with_session
    async def get_message(self,session: AsyncSession, admin_id: int,post_id: int) -> Optional[MessageObject] | None:
        stmt = await session.execute(
            select(MessageModel).where(
                and_(MessageModel.admin_id == admin_id,MessageModel.post_id == post_id)))
        result = stmt.scalars().first()
        if result:
            return MessageObject.model_validate(result.__dict__)
