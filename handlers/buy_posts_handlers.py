from aiogram.types import Message, CallbackQuery
from aiogram import F
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from utils.config import orm_services, orm_payments
from utils.keyboards import btn_pay_methods

buy_posts_router = Router()






