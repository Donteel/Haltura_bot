import logging

from adminka.admin_handlers import main_handlers, broadcast_handler, limit_remote_handlers
from handlers import vacancy_management
from utils.bot_instance import dp_admin, bot_admin


async def run_admin_bot():

    dp_admin.include_router(main_handlers.main_router)
    dp_admin.include_router(broadcast_handler.broadcast_router)
    dp_admin.include_router(limit_remote_handlers.limit_router)

    try:

        await bot_admin.delete_webhook(drop_pending_updates=True)
        await dp_admin.start_polling(bot_admin, dispatcher=dp_admin, polling_timeout=60)

    finally:
        # Закрываем сессию бота
        await bot_admin.session.close()
        logging.info('Admin bot session closed')