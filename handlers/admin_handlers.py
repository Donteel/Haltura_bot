import aiogram
from aiogram.exceptions import TelegramMigrateToChat
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram import F
from sqlalchemy.testing.plugin.plugin_base import logging

from middlewares.add_user_middleware import AddUserMiddleware
from middlewares.blacklist_middlewares import CheckBlackListMiddleWare
from middlewares.subscription_verification import SubscriptionVerificationMiddleware
from utils.keyboards import *
from aiogram import Router
from utils.state_models import AdminState
from utils.bot_instance import bot
from utils.config import action_orm, main_chat, orm_posts
from aiogram.fsm.context import FSMContext
from utils.other import state_for_user, schedule_cancel, post_publication, change_admin_message

admin_router = Router()


admin_router.message.middleware(CheckBlackListMiddleWare())
admin_router.callback_query.middleware(CheckBlackListMiddleWare())
admin_router.message.middleware(AddUserMiddleware())
admin_router.callback_query.middleware(AddUserMiddleware())
admin_router.message.middleware(SubscriptionVerificationMiddleware())
admin_router.callback_query.middleware(SubscriptionVerificationMiddleware())


@admin_router.callback_query(AdminState.action_blocked)
async def action_block(callback: CallbackQuery):
    await callback.answer('Этой вакансией занимается другой администратор,подождите обновлений.')


# Обработка принятия заявки
@admin_router.callback_query(F.data.startswith('adminConfirm_'))
async def confirm_post(callback: CallbackQuery, state: FSMContext):

    callback_data,post_id = callback.data.split('_')
    post_data = await orm_posts.get_post(int(post_id))

    await post_publication(post_id=int(post_id),chat_id=main_chat)

    admins_data = await action_orm.get_admins_id()

    await change_admin_message(admins_data=admins_data,
                               post_id=int(post_id),
                               verdict=callback_data
                               )


    user_state = await state_for_user(post_data.user_id)

    await user_state.clear()
    await state.clear()


# удаление предложенной вакансии
@admin_router.callback_query(F.data.startswith('adminDelete_'))    # noqa
async def delete_post(callback: CallbackQuery,state: FSMContext):

    callback_text,post_id = callback.data.split('_')

    admin_data = await action_orm.get_admins_id()

    await change_admin_message(admins_data=admin_data,
                               post_id=int(post_id),
                               verdict=callback_text
                               )

    await callback.message.answer('Пост пользователя будет отменён,'
                                  'укажите причину отмены для завершения обработки',
                                  reply_markup=ReplyKeyboardRemove())

    await state.set_state(AdminState.waiting_for_reason)

    await state.update_data(post_id=post_id)
    await callback.answer()


# отправка причины удаления пользователю
@admin_router.message(AdminState.waiting_for_reason,F.text)
async def cancel_post(message:Message, state: FSMContext):

    data = await state.get_data()
    post_data = await orm_posts.get_post(data['post_id'])
    reason_cancellation = message.text

    await bot.send_message(chat_id=post_data.user_id,
                           text="<b>Ваша вакансия не прошла проверку.</b>\n"
                                "Причина:\n"
                                f"{reason_cancellation}",
                           reply_markup=btn_home())

    user_state = await state_for_user(post_data.user_id)

    await user_state.clear()

    await orm_posts.changeStatus(post_data.id,'canceled')

    await state.clear()

    await message.answer('Причина отправлена пользователю!')


@admin_router.callback_query(F.data.startswith('postingCancel'))
async def cancel_posting(callback: CallbackQuery,state: FSMContext):
    callback_text,post_id = callback.data.split('_')
    post = await orm_posts.get_post(int(post_id))


    if schedule_cancel(post.job_id):
        admins_data = await action_orm.get_admins_id()
        await change_admin_message(admins_data=admins_data,
                                   post_id=int(post_id),
                                   verdict='postCancel'
                                   )
        await bot.send_message(text='<b>Ваша публикация отменена администратором!</b>\n'
                                    'подробнее - /help',
                               chat_id=post.user_id
                               )
        await orm_posts.remove_post(int(post_id))
        await state.clear()
        await callback.answer("Вакансия успешно отменена!")
    else:
        await callback.answer('Публикация уже опубликована или отменена ранее.')


@admin_router.callback_query(F.data.startswith('cancelAndBlock'))
async def cancel_posting_and_block(callback: CallbackQuery,state: FSMContext):

    callback_text, post_id = callback.data.split('_')
    post = await orm_posts.get_post(int(post_id))

    try:
        if schedule_cancel(post.job_id):

            admins_data = await action_orm.get_admins_id()

            await change_admin_message(admins_data=admins_data,
                                       post_id=int(post_id),
                                       verdict=callback_text
                                       )

            await action_orm.add_to_blacklist(post.user_id)

            await bot.send_message(text='<b>Вы добавлены в черный список!</b>\n'
                                        'Спасибо что были с нами!',
                                   chat_id=post.user_id,
                                   reply_markup=ReplyKeyboardRemove()
                                   )

            await orm_posts.remove_post(int(post_id))
            await state.clear()

        else:
            await callback.answer('Публикация уже опубликована или отменена ранее.')
    except AttributeError:
        await callback.answer('Задача не найдена',show_alert=True)
    await callback.answer()


@admin_router.callback_query(F.data.startswith('delAndBlock'))
async def delete_and_block(callback: CallbackQuery,state: FSMContext):
    callback_text,post_id = callback.data.split('_')
    post = await orm_posts.get_post(int(post_id))
    if post:
        await action_orm.add_to_blacklist(post.user_id)
    await delete_post(callback,state)

    await callback.answer('Пользователь добавлен в черный список!',show_alert=True)


# рассылка пользователям
@admin_router.message(Command('broadcast'))
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
@admin_router.message(F.text,AdminState.waiting_for_broadcast_ms)
async def send_broadcast(message: Message,state: FSMContext):
    blocked_count = 0
    all_users = await action_orm.get_users_ids()
    if all_users is not None:
        for user_id in all_users:
            try:
                if int(user_id) != message.from_user.id:
                    await message.bot.send_message(text=message.text,
                                                   chat_id=int(user_id)
                                                   )
            except aiogram.exceptions.TelegramForbiddenError as e:
                blocked_count += 1
                logging.error(f'Произошла ошибка {e} во время отправки сообщения пользователю')
        await message.answer(f'Я отправил сообщения всем пользователям.\n'
                             f'Кстати, вот количество пользователей которые заблокировали бота - <b>{blocked_count}</b>')
        await state.clear()
    else:
        await message.answer('Пользователи не найдены или возникла ошибка их извлечения',
                             reply_markup=btn_home()
                             )
