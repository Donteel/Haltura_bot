from aiogram.types import Message
from aiogram import F
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from utils.config import orm_services
from utils.keyboards import btn_services, btn_cancel
from utils.state_models import PaymentState

shop_router = Router()


# /shop см. buy_limits_for_user в handlers/user_handlers.py:131



@shop_router.message(F.text.regexp(r'[^@\s]+@[^@\s]+\.[^@\s]+'), PaymentState.awaiting_email)
async def get_email_for_payment(message: Message, state: FSMContext):

    await state.update_data(email=message.text)

    services: list[tuple] = await orm_services.get_services()

    await message.answer('<b>Выберите интересующую вас услугу:</b>',
                         reply_markup=btn_services(services))

    await state.set_state(PaymentState.payment_state)


@shop_router.message(~F.text.regexp(r'[^@\s]+@[^@\s]+\.[^@\s]+'), PaymentState.awaiting_email)
async def if_not_email(message: Message, state: FSMContext):

    await message.answer("Ввод не понятен, повторите попытку!",
                         reply_markup=btn_cancel()
                         )
