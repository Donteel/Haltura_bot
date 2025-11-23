from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from utils.config import storage, bot_token

dp = Dispatcher(storage=storage)
bot=Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))