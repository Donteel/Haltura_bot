import logging
from functools import wraps
from typing import Sequence, Optional
from sqlalchemy import and_, Row
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from DataBase.BaseModel import UserModel, engine,PostModel, AdminModel, BlackListModel, MessageModel
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from DataBase.MessageObject import MessageObject
from DataBase.postObject import PostObject
from DataBase.userObject import UserObject

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def with_session(func):
    """Декоратор для автоматического создания и закрытия сессии"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):  # `self` здесь будет передан автоматически
        async with self.session_factory() as session:
            try:
                return await func(self, session, *args, **kwargs)  # Передаём `session`
            except Exception as e:
                await session.rollback()
                logging.error(f"Ошибка в {func.__name__}: {e}")
                raise
    return wrapper


class UserManagementBase:

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
    async def create_user(self,session: AsyncSession,tg_id,username):

        user = UserModel(id=tg_id,username=username)

        try:
            session.add(user)
            await session.commit()
            return True
        except IntegrityError as e:
            logging.error(e)
            await session.rollback()
            return False


    @with_session
    async def get_user(self,session: AsyncSession,tg_id):

        stmt = await session.execute(select(UserModel).where(UserModel.id==tg_id))
        result = stmt.scalar_one_or_none()
        if result:
            return result
        else:
            return False



    @with_session
    async def get_users_ids(self, session: AsyncSession):
        stmt = await session.execute(select(UserModel.id))
        result = stmt.scalars().all()
        logging.info('Я получил ID всех пользователей в таком формате:\n'
                     f'{result}')
        return result

    @with_session
    async def get_admins(self,session: AsyncSession) -> Sequence[Row[tuple[str, str]]]:
        admins = await session.execute(select(AdminModel.user_name,AdminModel.admin_role))
        result = admins.fetchall()
        return result


    @with_session
    async def get_admins_id(self,session: AsyncSession) -> list[int]:
        stmt = await session.execute(select(AdminModel.id))
        result = stmt.scalars().all()
        return [admin_id for admin_id in result]


    @with_session
    async def add_to_blacklist(self,session: AsyncSession,tg_id):
        user = BlackListModel(user_id=tg_id)
        try:
            session.add(user)
            await session.commit()
            return True
        except IntegrityError as e:
            logging.error(e)
            await session.rollback()
            return False

    @with_session
    async def remove_from_blacklist(self,session: AsyncSession,tg_id):
        stmt = session.execute(select(BlackListModel).where(BlackListModel.user_id == tg_id))
        try:
            await session.delete(stmt)
            await session.commit()
            return True
        except InvalidRequestError as e:
            await session.rollback()
            logging.info(f'Ошибка при удалении пользователя из черного списка\n'
                         f'{e}'
                         )
            return False

    @with_session
    async def get_user_from_blacklist(self,session: AsyncSession,tg_id):
        stmt = await session.execute(select(BlackListModel).where(BlackListModel.user_id == tg_id))
        stmt = stmt.scalars().first()
        if stmt is None:
            return False
        user = UserObject.model_validate(stmt.__dict__)
        return user


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
    async def changeStatus(self,session: AsyncSession,post_id,status):
        stmt = await session.execute(select(PostModel).where(PostModel.id == post_id))
        result = stmt.scalars().first()
        if result:
            result.status = status
            await session.commit()
            return True
        await session.rollback()
        return False

    @with_session
    @with_session
    @with_session

    @with_session
    async def post_deactivate(self,session: AsyncSession,post_id):


        post = await session.execute(
            select(PostModel).where(
                PostModel.id == post_id)
        )

        result = post.scalars().first()

        result.status = 'deactivate'

        await session.commit()

        return result




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
                                    post_id=ms_obj.temp_id,
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
