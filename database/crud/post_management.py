import logging
import zoneinfo
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select, and_, func

from database.base_model import PostModel
from database.objects.post_object import PostObject
from database.session_config import AsyncSessionLocal, with_session


class PostManagementBase:

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
    async def create_new_post(self,session: AsyncSession,post_text,user_id,username):

        post = PostModel(
            post_text= post_text,
            user_id = user_id,
            username=username
        )

        try:
            session.add(post)
            await session.commit()
            return post.id

        except Exception as e:
            logging.error(e)
            await session.rollback()


    @with_session
    async def get_post(self,session: AsyncSession, post_id) -> Optional[PostObject | None]:
        """
        Метод для получения данных уже опубликованного поста
        :param session: Объект сессии
        :param post_id: ID публикации
        """

        stmt = await session.execute(select(PostModel).where(PostModel.id == post_id))

        if data := stmt.scalars().first():
            return PostObject.model_validate(data.__dict__)
        return None


    @with_session
    async def check_post_by_msg_id(self,session: AsyncSession, message_id,user_id):
        stmt = await session.execute(
            select(PostModel).where(
                and_(PostModel.message_id == message_id,PostModel.user_id == user_id)
            )
        )

        if data := stmt.scalars().first():
            return PostObject.model_validate(data.__dict__)
        return None


    @with_session
    async def addJobId_to_post(self,session: AsyncSession,post_id:int,job_id: str):
        """
        Метод добавляет JobID к записи поста
        :param session: объект сессии
        :param post_id: Id поста
        :param job_id: job_id задачи на публикацию
        :return: bool
        """
        stmt = await session.execute(
            select(PostModel).where(PostModel.id == post_id)
            )

        result = stmt.scalars().first()
        if result:
            result.job_id = job_id
            await session.commit()
            return True
        return False


    @with_session
    async def addMessageId_to_post(self,session: AsyncSession,post_id:int,message_id:int):
        """
        Метод добавляет message_id к записи на публикации.
        :param session: объект сессии
        :param post_id: id записи в бд
        :param message_id: message_id публикации
        :return: bool
        """
        stmt = await session.execute(select(PostModel).where(PostModel.id == post_id))
        result = stmt.scalars().first()
        if result:
            result.message_id = message_id
            await session.commit()
            return True
        return False


    @with_session
    async def remove_post(self,session: AsyncSession,post_id):
        stmt = await session.execute(select(PostModel).where(PostModel.id == post_id))
        result = stmt.scalars().first()
        if result:
            await session.delete(result)
            await session.commit()
            return True
        await session.rollback()
        return False


    @with_session
    async def change_post_status(self, session: AsyncSession, post_id, status):
        stmt = await session.execute(select(PostModel).where(PostModel.id == post_id))
        result = stmt.scalars().first()
        if result:
            result.status = status
            await session.commit()
            return True
        await session.rollback()
        return False


    @with_session
    async def post_deactivate(self,session: AsyncSession,post_id):


        post = await session.execute(
            select(PostModel).where(
                PostModel.id == post_id)
        )

        result = post.scalars().first()

        result.status = 'deactivate'
        result.job_id = None

        await session.commit()

        return result


    @with_session
    async def get_post_count(self,session: AsyncSession,user_id,):

        now = datetime.now(zoneinfo.ZoneInfo('Europe/Moscow'))

        # Просто создаем границы сегодняшнего дня
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_finish = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        stmt = await session.execute(
            select(
                func.count(PostModel.id)
            ).where(
                and_(
                    PostModel.user_id == user_id,
                    PostModel.created_at >= day_start,
                    PostModel.created_at <= day_finish,
                    PostModel.message_id != None
                )
            )
        )

        return stmt.scalar()
