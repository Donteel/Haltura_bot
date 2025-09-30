import logging
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from database.base_model import engine

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
