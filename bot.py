from handlers import user_handlers, new_post_handlers, admin_handlers, limit_remote_handlers
from database.base_model import create_tables
from utils.schedule_tasks import scheduler
from utils.bot_instance import dp, bot
import asyncio
import logging


async def main():

    dp.include_router(user_handlers.user_router)
    dp.include_router(admin_handlers.admin_router)
    dp.include_router(new_post_handlers.create_post_router)
    dp.include_router(limit_remote_handlers.limit_router)

    await create_tables()
    scheduler.start()

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