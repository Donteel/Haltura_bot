import logging
import zoneinfo
from datetime import datetime
from functools import wraps
from typing import Sequence, Optional
from sqlalchemy import and_, Row, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import Mapped
from database.base_model import UserModel, engine, PostModel, AdminModel, BlackListModel, MessageModel, UserLimitsModel, \
    ExtraLimitsModel, LimitLogsModel
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from database.limit_object import LimitObject
from database.message_object import MessageObject
from database.post_object import PostObject
from database.user_object import UserObject

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def with_session(function):
    """Декоратор для автоматического создания и закрытия сессии"""
    @wraps(function)
    async def wrapper(self, *args, **kwargs):  # `self` здесь будет передан автоматически
        async with self.session_factory() as session:
            try:
                return await function(self, session, *args, **kwargs)  # Передаём `session`
            except Exception as e:
                await session.rollback()
                logging.error(f"Ошибка в {function.__name__}: {e}")
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

    @staticmethod
    async def get_day_range():

        now = datetime.now()

        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_finish = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        return day_start, day_finish

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


    @with_session
    async def create_user_limit(self,session: AsyncSession,user_id:int,limit:int) -> bool | int:

        day_start, day_finish = await self.get_day_range()

        # получить данные о лимите, и проверить последнюю дату обновления.
        stmt = await session.execute(
            select(UserLimitsModel).where(
                UserLimitsModel.user_id == user_id
            )
        )

        user_limit = stmt.scalar_one_or_none()

        # если записей нет
        if user_limit is None:
            # если данных о лимите нет значит пользователя еще нет в таблице лимитов
            # создаем новую запись и даем новые лимиты

            new_limit = UserLimitsModel(user_id=user_id)

            try:
                session.add(new_limit)
                await session.commit()
                return new_limit.daily_limit

            except IntegrityError as e:
                await session.rollback()
                logging.error('Ошибка при создании лимита для пользователя:\n\n'
                              f'{e.__dict__}')
                raise ValueError

        # если запись есть, но она устарела

        elif user_limit.created_at<day_start:

            # обновляем лимиты и все
            user_limit.daily_limit = limit
            user_limit.created_at = datetime.now(zoneinfo.ZoneInfo('Europe/Moscow'))

            try:
                session.add(user_limit)
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                logging.error("Произошла ошибка обновления устаревшего лимита",e.__dict__)
                raise IntegrityError
        else:
            pass

    @with_session
    async def get_user_limit(self, session: AsyncSession, user_id) -> Mapped[int] | None:
        stmt = await session.execute(
            select(UserLimitsModel).where(
                UserLimitsModel.user_id == user_id
            )
        )
        user_limit = stmt.scalars().first()

        if user_limit:
            return user_limit.daily_limit
        return None


    @with_session
    async def get_extra_limit(self, session: AsyncSession, user_id) -> Mapped[int] | int:
        stmt = await session.execute(
            select(ExtraLimitsModel).where(
                ExtraLimitsModel.user_id == user_id
            )
        )
        extra_limit = stmt.scalars().first()

        if extra_limit:
            return extra_limit.daily_limit
        return 0


    @with_session
    async def change_extra_limit(self, session: AsyncSession,
                                 user_id: int,
                                 action:str=False,
                                 limit=None) -> Mapped[int] | int:

        # получаем объект лимита пользователя
        stmt = await session.execute(
            select(ExtraLimitsModel).where(
                ExtraLimitsModel.user_id == user_id
            )
        )
        extra_limit = stmt.scalar_one_or_none()

        if extra_limit:
            try:
                match action:
                    case "minus":
                        if extra_limit.daily_limit <= 0:
                            pass
                        else:
                            extra_limit.daily_limit -= limit if limit else 1
                    case "plus":
                        extra_limit.daily_limit += limit if limit else 1

                await session.commit()
                return True
            except Exception as e:
                logging.error(f"Ошибка добавления лимита {limit}",
                              e.__dict__)
                return False
        else:
            extra_limit = ExtraLimitsModel(
                user_id=user_id,
                daily_limit=limit if limit >= 0 else 0
            )
            try:
                session.add(extra_limit)
                await session.commit()
            except Exception as e:
                logging.error("Не удалось добавить запись о дополнительных лимитах пользователя",
                              e.__dict__
                              )

    @staticmethod
    def choice_limit_type(daily_limit,extra_limit):
        limit_type = ""

        if daily_limit.daily_limit > 0:
            limit_type = 'daily'
        else:
            if extra_limit.daily_limit > 0:
                limit_type = 'extra'

        return limit_type


    @with_session
    async def change_user_limit(self,session: AsyncSession,
                                user_id,
                                post_id: int,
                                action: str,
                                quantity:int = False,
                                ) -> None:
        """
        Метод для динамического управления лимитом пользователя.
        """


        log_data = {
            "type": "",
            "post_id": post_id,
            "user_id": user_id,
            "status": ""
        }

        stmt_1 = await session.execute(
            select(UserLimitsModel).where(
                UserLimitsModel.user_id == user_id
            )
        )

        stmt_2 = await session.execute(
            select(ExtraLimitsModel).where(
                ExtraLimitsModel.user_id == user_id
            )
        )

        daily_limit = stmt_1.scalar_one_or_none()
        extra_limit = stmt_2.scalar_one_or_none()

        # определение типа лимита
        limit_type = self.choice_limit_type(daily_limit, extra_limit)

        match action:
            # удаление лимитов
            case "minus":

                status = "deleted"

                if limit_type == "daily":
                    # отнимаем нужное количество
                    daily_limit.daily_limit -= 1
                    await session.commit()

                elif limit_type == "extra":
                    # отнимаем нужное количество
                    extra_limit.daily_limit -= 1
                    await session.commit()

                # определяем данные для логирования
                log_data["type"] = limit_type
                log_data["status"] =  status

                log_obj = LimitObject.model_validate(log_data)

                await self.add_limit_log(log_obj)

            # возвращение лимитов
            case "plus":
                status = "added"
                log_obj = await self.get_limit_log(
                    post_id=post_id,
                    user_id=user_id
                )
                if log_obj.type == 'daily':
                    daily_limit.daily_limit += quantity if quantity else 1

                elif log_obj.type == 'extra':
                    extra_limit.daily_limit += quantity if quantity else 1

                    # определяем данные для логирования
                    log_data["type"] = limit_type
                    log_data["status"] = status

                    log_obj = LimitObject.model_validate(log_data)

                    await self.add_limit_log(log_obj)

                await session.commit()

            case False:
                pass




    @with_session
    async def add_limit_log(self,
                            session:AsyncSession,
                            limit_obj: LimitObject) -> LimitObject | None:

        limit_log = LimitLogsModel(
            user_id=limit_obj.user_id,
            post_id=limit_obj.post_id,
            type=limit_obj.type,
            status=limit_obj.status
        )
        try:
            session.add(limit_log)
            await session.commit()

            limit_log = LimitObject.model_validate(limit_log.__dict__)
            return limit_log

        except Exception as e:
            logging.error("Ошибка добавления лога для лимита",
                          e.__dict__
                          )

    @with_session
    async def get_limit_log(self,session:AsyncSession,
                            post_id:int,
                            user_id:int) -> LimitObject | None:
        stmt = await session.execute(
            select(LimitLogsModel).where(
                and_(
                    LimitLogsModel.post_id == post_id,
                    LimitLogsModel.user_id == user_id
                )
            )
        )

        user_log = stmt.scalar_one_or_none()
        user_log = LimitObject.model_validate(user_log.__dict__)

        return user_log



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
