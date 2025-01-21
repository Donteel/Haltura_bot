import logging
from sqlalchemy import func, and_, Row
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from DataBase.BaseModel import UserModel, engine, TempPostModel, PostModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, NoResultFound


AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class ActionModel:
    def __init__(self):
        self.session_factory = AsyncSessionLocal


    async def create_user(self,tg_id,username):
        async with self.session_factory() as session:
            user = UserModel()
            user.user_id = tg_id
            user.username = username
            try:
                session.add(user)
                await session.commit()
                return True
            except IntegrityError as e:
                logging.error(e)
                await session.rollback()
                return False


    async def create_new_post(self,post_text,user_id,message_id):
        async with self.session_factory() as session:
            post = PostModel()
            post.post_text = post_text
            post.user_id = user_id
            post.message_id = message_id
            try:
                session.add(post)
                await session.commit()
                return post.id
            except Exception as e:
                logging.error(e)
                await session.rollback()

    async def get_post(self,message_id,user_id):
        async with self.session_factory() as session:
            stmt = await session.execute(select(PostModel).where(and_(PostModel.message_id == message_id,PostModel.user_id == user_id)))
            if data := stmt.scalars().first():
                return {'post_text':data.post_text,'user_id':data.user_id,'id':data.id,'message_id':data.message_id}
            return None


    async def post_deactivate(self,message_id,user_id):
        async with self.session_factory() as session:

            post = await session.execute(
                select(PostModel).where(and_(
                    PostModel.message_id == message_id,PostModel.user_id == user_id)
                )
            )
            result = post.scalars().first()
            result.status = False
            await session.commit()
            return result

    async def create_temp_post(self,post_text,user_id,username):
        async with self.session_factory() as session:
            temp_post = TempPostModel(post_text= post_text,
                                      user_id= user_id,
                                      username= username
                                      )

            try:
                session.add(temp_post)
                await session.commit()
                return temp_post.id
            except Exception as e:
                logging.error(e)
                await session.rollback()


    async def get_temp_post(self,post_id):
        async with self.session_factory() as session:
            stmt = await session.execute(select(TempPostModel).where(TempPostModel.id == post_id))
            if data := stmt.scalars().first():
                return {'post_text':data.post_text,'user_id':data.user_id,'id':data.id,'username':data.username}
            return None

    async def remove_temp_post(self,post_id):
        async with self.session_factory() as session:
            stmt = await session.execute(select(TempPostModel).where(TempPostModel.id == post_id))
            await session.delete(stmt.scalars().first())
            await session.commit()
            return True


