from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from Handlers import user_handlers, createNewPostHandlers, admin_handlers
from DataBase.BaseModel import create_tables
from Utils.config import bot_token
import asyncio
import logging
from Utils.config import storage



async def main():
    dp = Dispatcher(storage=storage)
    bot=Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(user_handlers.user_router)
    dp.include_router(admin_handlers.admin_router)
    dp.include_router(createNewPostHandlers.create_post_router)
    await create_tables()
    try:
        logging.info('все таблицы созданы')
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, dispatcher=dp, polling_timeout=60)
    finally:
        await bot.session.close()  # Закрываем сессию бота
        logging.info('Bot session closed')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Shutting down bot...')