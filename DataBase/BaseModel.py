import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncAttrs, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import ForeignKey, func, BigInteger

engine = create_async_engine('sqlite+aiosqlite:///haltura_base.db',echo=True) # noqa
# Настройка движка и фабрики сессий
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class AbstractModel(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

class UserModel(AbstractModel):
    __tablename__ = 'users' # noqa

    id = mapped_column(BigInteger,nullable=False,unique=True,primary_key=True)
    username: Mapped[str] = mapped_column(nullable=True)


class TempPostModel(AbstractModel):
    __tablename__ = 'temp_post' # noqa
    user_id:Mapped[int] = mapped_column(ForeignKey(UserModel.id,ondelete='CASCADE'),nullable=False)
    username:Mapped[str] = mapped_column(nullable=True)
    post_text: Mapped[str] = mapped_column(nullable=False)

class PostModel(AbstractModel):
    __tablename__ = 'post'  # noqa

    user_id: Mapped[int] = mapped_column(ForeignKey(UserModel.id, ondelete='CASCADE'))
    post_text: Mapped[str] = mapped_column(nullable=False)
    message_id:Mapped[int] = mapped_column(nullable=False)
    status: Mapped[bool] = mapped_column(nullable=False,default=True)


class BlackListModel(AbstractModel):
    __tablename__ = 'blacklist' # noqa
    user_id:Mapped[int] = mapped_column(ForeignKey(UserModel.id, ondelete='CASCADE'))

class AdminModel(AbstractModel):

    __tablename__ = 'admin' # noqa
    id = mapped_column(BigInteger,nullable=False,unique=True,primary_key=True)
    user_name:Mapped[str] = mapped_column(nullable=False)
    admin_role: Mapped[str] = mapped_column(nullable=False)




async def create_tables():
    # Создание всех таблиц на основе моделей
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)