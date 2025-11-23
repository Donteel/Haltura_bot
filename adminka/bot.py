import asyncio
import logging

from admin_handlers import main_handlers, broadcast_handler, limit_remote_handlers
from ad_utils.bot_instance import dp,bot
from database.base_model import create_tables


async def main():

    dp.include_router(main_handlers.main_router)
    dp.include_router(broadcast_handler.broadcast_router)
    dp.include_router(limit_remote_handlers.limit_router)

    await create_tables()

    try:

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, dispatcher=dp, polling_timeout=60)

    finally:
        # Закрываем сессию бота
        await bot.session.close()
        logging.info('Admin bot session closed')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Shutting down bot...')