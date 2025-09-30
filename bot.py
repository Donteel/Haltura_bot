from adminka.Admin_bot import run_admin_bot
from database.base_model import create_tables

from handlers import vacancy_management, shop_handlers, buy_posts_handlers
from handlers import user_handlers, new_post_handlers

from utils.schedule_tasks import scheduler
from utils.bot_instance import dp, bot

import asyncio
import logging

async def run_user_bot():

    dp.include_router(user_handlers.user_router)
    dp.include_router(new_post_handlers.create_post_router)
    dp.include_router(shop_handlers.shop_router)
    dp.include_router(vacancy_management.vacancy_router)
    dp.include_router(buy_posts_handlers.buy_posts_router)

    try:

        await bot.delete_webhook(drop_pending_updates=True)

        await dp.start_polling(bot, dispatcher=dp, polling_timeout=60)

    finally:
        await bot.session.close()  # Закрываем сессию бота
        logging.info('Bot session closed')


async def main():


    await create_tables()
    scheduler.start()

    logging.info('все таблицы созданы')


    await asyncio.gather(
        run_user_bot(),
        run_admin_bot()
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Shutting down bot...')