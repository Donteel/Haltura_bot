import logging

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.testing.pickleable import Order

from database.base_model import ServiceModel, OrdersModel
from database.objects.service_object import ServiceObject
from database.session_config import AsyncSessionLocal, with_session


class ServiceManagement:

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
    async def get_services(self, session: AsyncSession):
        stmt = await session.execute(
            select(
                ServiceModel.id,
                ServiceModel.service_name,
                ServiceModel.service_price,
                ServiceModel.quan
            )
        )

        result = stmt.fetchall()
        return result

    @with_session
    async def get_service_by_id(self, session: AsyncSession, service_id: int):
        stmt = await session.execute(
            select(ServiceModel).where(ServiceModel.id == service_id)
        )


        result = stmt.scalars().first()

        service = ServiceObject.model_validate(result.__dict__)

        return service if service else None

    @with_session
    async def create_new_order(self,
                               session: AsyncSession,
                               user_id,
                               uuid,
                               pay_method,
                               order_amount,
                               created_at,
                               status):

        order = OrdersModel(user_id=user_id,
                            order_uuid=uuid,
                            payment_method=pay_method,
                            order_amount=order_amount,
                            created_at=created_at,
                            status=status)
        try:
            session.add(order)
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.error('error creating order', exc_info=e)
            raise e
