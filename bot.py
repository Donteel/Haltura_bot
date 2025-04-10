from Handlers import user_handlers, createNewPostHandlers, admin_handlers
from DataBase.BaseModel import create_tables
from Utils.ScheduleTasks import scheduler
from Utils.bot_instance import dp, bot
import asyncio
import logging


async def main():

    dp.include_router(user_handlers.user_router)
    dp.include_router(admin_handlers.admin_router)
    dp.include_router(createNewPostHandlers.create_post_router)
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