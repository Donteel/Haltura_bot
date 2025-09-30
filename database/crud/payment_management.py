from sqlalchemy.sql.expression import select

from database.base_model import PaymentMethodsModel, ServiceModel
from database.session_config import with_session, AsyncSession, AsyncSessionLocal


class PaymentManagementBase:
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
    async def get_payment_methods(self,session: AsyncSession):
        stmt = await session.execute(
            select(
                PaymentMethodsModel.id,PaymentMethodsModel.payment_name
            )
        )

        result = stmt.fetchall()
        return result