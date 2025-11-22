import aiogram
from aiogram.exceptions import TelegramMigrateToChat
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram import F

from middlewares.add_user_middleware import AddUserMiddleware

from utils.keyboards import *
from utils.state_models import AdminState
from utils.config import action_orm



# noinspection DuplicatedCode
broadcast_router = Router()


broadcast_router.message.middleware(AddUserMiddleware())
broadcast_router.callback_query.middleware(AddUserMiddleware())


# рассылка пользователям
@broadcast_router.message(Command('broadcast'))
async def broadcast(message: Message,state: FSMContext):
    if message.from_user.id in await action_orm.get_admins_id():
        await message.answer('Давай отправим сообщение всем пользователям.\n'
                             'Жду твоего сообщения для рассылки...',
                             reply_markup=btn_cancel()
                             )
        await state.set_state(AdminState.waiting_for_broadcast_ms)
    else:
        await message.answer('Вам не доступна эта команда.',reply_markup=btn_home())


# исполнение рассылки
@broadcast_router.message(F.text,AdminState.waiting_for_broadcast_ms)
async def send_broadcast(message: Message,state: FSMContext):
    blocked_count = 0
    users_count = 0
    all_users = await action_orm.get_users_ids()
    if all_users is not None:
        for user_id in all_users:
            try:
                if int(user_id) != message.from_user.id:
                    await message.bot.send_message(text=message.text,
                                                   chat_id=int(user_id)
                                                   )
                    users_count += 1
            except aiogram.exceptions.TelegramForbiddenError as e:
                blocked_count += 1

                logging.error(f'Произошла ошибка {e} во время отправки сообщения пользователю')

        await message.answer(f'Я отправил сообщения всем пользователям.({users_count})\n'
                             f'Кстати, вот количество пользователей которые заблокировали бота - <b>{blocked_count}</b>',
                             reply_markup=btn_home())
        await state.clear()
    else:
        await message.answer('Пользователи не найдены или возникла ошибка их извлечения',
                             reply_markup=btn_home()
                             )
