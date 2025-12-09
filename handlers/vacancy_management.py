import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from middlewares.add_user_middleware import AddUserMiddleware
from middlewares.blacklist_middlewares import CheckBlackListMiddleWare
from middlewares.subscription_verification import SubscriptionVerificationMiddleware

from utils.bot_instance import bot
from utils.config import orm_posts, main_chat, action_orm
from utils.keyboards import btn_home
from utils.other import post_publication, change_admin_message, state_for_user, schedule_cancel
from utils.state_models import AdminState

# noinspection DuplicatedCode
vacancy_router = Router()


vacancy_router.message.middleware(CheckBlackListMiddleWare())
vacancy_router.callback_query.middleware(CheckBlackListMiddleWare())
vacancy_router.message.middleware(AddUserMiddleware())
vacancy_router.callback_query.middleware(AddUserMiddleware())
vacancy_router.message.middleware(SubscriptionVerificationMiddleware())
vacancy_router.callback_query.middleware(SubscriptionVerificationMiddleware())



@vacancy_router.callback_query(AdminState.action_blocked)
async def action_block(callback: CallbackQuery):
    await callback.answer('Этой вакансией занимается другой администратор,подождите обновлений.')


# Обработка принятия заявки
@vacancy_router.callback_query(F.data.startswith('adminConfirm_'))
async def confirm_post(callback: CallbackQuery, state: FSMContext):

    callback_data,post_id = callback.data.split('_')
    post_data = await orm_posts.get_post(int(post_id))

    await post_publication(post_id=int(post_id),chat_id=main_chat)

    admins_data = await action_orm.get_admins_id()

    await change_admin_message(admins_data=admins_data,
                               post_id=int(post_id),
                               verdict=callback_data
                               )

    # отнимаем 1 публикацию пользователя
    await action_orm.change_user_limit(user_id=post_data.user_id,
                                       post_id=post_id,
                                       action="minus"
                                       )


    user_state = await state_for_user(post_data.user_id)

    await user_state.clear()
    await state.clear()


# удаление предложенной вакансии
@vacancy_router.callback_query(F.data.startswith('adminDelete_'))    # noqa
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
@vacancy_router.message(AdminState.waiting_for_reason,F.text)
async def cancel_post(message:Message, state: FSMContext):

    data = await state.get_data()
    post_data = await orm_posts.get_post(data['post_id'])
    reason_cancellation = message.text

    await bot.send_message(chat_id=post_data.user_id,
                           text="<b>Ваша вакансия не прошла проверку.</b>\n"
                                "Причина:\n"
                                f"{reason_cancellation}",
                           reply_markup=btn_home())

    # # добавляем лимит обратно
    # await action_orm.change_user_limit(
    #     user_id=post_data.user_id,
    #     post_id=post_data.id,
    #     action="plus"
    # )

    user_state = await state_for_user(post_data.user_id)

    await user_state.clear()

    await orm_posts.change_post_status(post_data.id, 'canceled')

    await state.clear()

    await message.answer('Причина отправлена пользователю!')


@vacancy_router.callback_query(F.data.startswith('postingCancel'))
async def cancel_posting(callback: CallbackQuery,state: FSMContext):
    callback_text,post_id = callback.data.split('_')
    post = await orm_posts.get_post(int(post_id))

    try:
        if schedule_cancel(post.job_id):
            admins_data = await action_orm.get_admins_id()
            await change_admin_message(admins_data=admins_data,
                                       post_id=int(post_id),
                                       verdict='postCancel'
                                       )
            await bot.send_message(text='<b>Ваша публикация отменена администратором!</b>\n'
                                        'Вы можете снова воспользоваться лимитом.'
                                        'подробнее - /help',
                                   chat_id=post.user_id
                                   )
            await orm_posts.post_deactivate(int(post_id))

            # добавляем лимит обратно
            await action_orm.change_user_limit(user_id=post.user_id,
                                               post_id=post.id,
                                               action="plus"
                                            )

            await state.clear()
            await callback.answer("Вакансия успешно отменена!")
        else:
            await callback.answer('Публикация уже опубликована или отменена ранее.')

    except AttributeError:
        await callback.answer('Публикация уже опубликована или отменена ранее.')


@vacancy_router.callback_query(F.data.startswith('cancelAndBlock'))
async def cancel_posting_and_block(callback: CallbackQuery,state: FSMContext):

    callback_text, post_id = callback.data.split('_')

    post = await orm_posts.get_post(int(post_id))

    admins_data = await action_orm.get_admins_id()

    # добавляем пользователя в чс
    await action_orm.add_to_blacklist(post.user_id)

    logging.info('Пользователь добавлен в чс')

    await bot.send_message(text='<b>Вы добавлены в черный список!</b>\n'
                                'Спасибо что были с нами!',
                           chat_id=post.user_id,
                           reply_markup=ReplyKeyboardRemove()
                           )


    # пробуем удалить задачу если она существует

    if schedule_cancel(post.job_id):
        logging.info("Задача на публикацию вакансии отменена")

    else:

        logging.info("Задача на публикацию отсутствует")


        # пробуем удалить пост с канала
        try:
            await bot.delete_message(chat_id=main_chat,message_id=int(post.message_id))

            logging.info("пост пользователя удален с канала")

            await callback.message.answer('Вакансия пользователя удалена с канала')

        except Exception as e:
            logging.info("пост пользователя не удален с канала", exc_info=e)

    await change_admin_message(admins_data=admins_data,
                               post_id=int(post_id),
                               verdict=callback_text
                               )
    await state.clear()


@vacancy_router.callback_query(F.data.startswith('delAndBlock'))
async def delete_and_block(callback: CallbackQuery,state: FSMContext):
    callback_text,post_id = callback.data.split('_')
    post = await orm_posts.get_post(int(post_id))
    if post:
        await action_orm.add_to_blacklist(post.user_id)
    await delete_post(callback,state)

    await callback.answer('Пользователь добавлен в черный список!',show_alert=True)
