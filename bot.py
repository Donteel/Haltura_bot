from aiogram import Bot, Dispatcher
import os
from Base.DataBase import create_tables
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from Utils.config import bot_token
import asyncio
import logging




async def main():
    dp = Dispatcher()
    bot=Bot(token=bot_token, parse_mode=ParseMode.HTML)