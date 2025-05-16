import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncAttrs, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
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

class PostModel(AbstractModel):
    __tablename__ = 'post'  # noqa

    user_id: Mapped[int] = mapped_column(ForeignKey(UserModel.id, ondelete='CASCADE'))
    username: Mapped[str] = mapped_column(nullable=True)
    post_text: Mapped[str] = mapped_column(nullable=False)
    message_id:Mapped[int] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=False,default='pending')
    job_id: Mapped[str] = mapped_column(nullable=True)


class BlackListModel(AbstractModel):
    __tablename__ = 'blacklist' # noqa
    user_id:Mapped[int] = mapped_column(ForeignKey(UserModel.id, ondelete='CASCADE'))


class AdminModel(AbstractModel):

    __tablename__ = 'admin' # noqa
    id = mapped_column(BigInteger,nullable=False,unique=True,primary_key=True)
    user_name:Mapped[str] = mapped_column(nullable=False)
    admin_role: Mapped[str] = mapped_column(nullable=False)

    message_ids = relationship("MessageModel", back_populates="admins")


class MessageModel(AbstractModel):
    __tablename__ = "messages"  # noqa

    admin_id = mapped_column(BigInteger,ForeignKey(AdminModel.id,ondelete='CASCADE'), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey(PostModel.id,ondelete='CASCADE'), nullable=False)
    message_id: Mapped[int] = mapped_column(nullable=False)

    admins = relationship("AdminModel",back_populates="message_ids")


async def create_tables():
    # Создание всех таблиц на основе моделей
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)