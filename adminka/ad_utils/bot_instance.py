from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import admin_token
from utils.config import storage

dp = Dispatcher(storage=storage)
bot = Bot(token=admin_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))