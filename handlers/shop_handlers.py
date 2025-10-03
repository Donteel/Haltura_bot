from aiogram.types import Message
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from utils.config import orm_services
from utils.keyboards import btn_services

shop_router = Router()


@shop_router.message(Command('shop'))
async def buy_limits_for_user(message: Message, state: FSMContext):

    services: list[tuple] = await orm_services.get_services()

    await message.answer('<b>Выберите интересующую вас услугу:</b>',
                         reply_markup=btn_services(services))


