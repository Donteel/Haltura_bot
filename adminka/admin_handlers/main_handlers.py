from aiogram.exceptions import TelegramMigrateToChat
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram import F

from handlers.user_handlers import cancel_func
from middlewares.add_user_middleware import AddUserMiddleware

main_router = Router()

main_router.message.middleware(AddUserMiddleware())
main_router.callback_query.middleware(AddUserMiddleware())

@main_router.message(Command("start"))
async def start(message: Message):
    await message.answer("<b>Ты в панели администратора!</b>")

@main_router.message(F.text == '❌ Отменить')
async def cancel_func(message: Message,state: FSMContext):
    await state.clear()
    await message.answer('Действие отменено!',reply_markup=ReplyKeyboardRemove())