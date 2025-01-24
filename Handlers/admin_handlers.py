from aiogram.exceptions import TelegramMigrateToChat
from aiogram.types import Message, CallbackQuery
from aiogram import F
from sqlalchemy.testing.plugin.plugin_base import logging
from Utils.Keyboards import *
from aiogram import Router
from Utils.StateModel import AdminState
from Utils.config import action_orm, main_chat
from aiogram.fsm.context import FSMContext
from Utils.other import state_for_user, clearing_of_all_states

admin_router = Router()



@admin_router.callback_query(F.data.regexp(r'admin_confirm_\d+$'),AdminState.waiting_action)
async def confirm_post(callback: CallbackQuery,state: FSMContext):

    # Получаем нужные данные
    temp_post_id = callback.data.split('_')[-1] # ID Поста
    temp_data: dict = await action_orm.get_temp_post(temp_post_id)
    post = temp_data['post_text'] # текст поста
    user_id = temp_data['user_id'] #user_id поста
    username = temp_data['username']


    # Отправляем сообщение в канал
    try:
        message_object = await callback.bot.send_message(chat_id=main_chat, text=post)
        chat_id = main_chat
    except TelegramMigrateToChat as e:
        # Если произошел перенос чата
        chat_id = e.migrate_to_chat_id
        message_object = await callback.bot.send_message(chat_id=chat_id, text=post)

    # Сохраняем идентификаторы сообщения и чата
    message_id = message_object.message_id

    # Логируем данные для отладки
    logging.info(f"Сообщение отправлено: chat_id={chat_id}, message_id={message_id}")

    # отправляем подтверждение пользователю
    await callback.bot.send_message(chat_id=user_id,text=f"<b>Ваш пост одобрен и успешно размещен!</b>\n"
                                                         f"<b>Номер поста:</b> <i>{message_id} (он понадобится если вы захотите </i>"
                                                         f"<i>деактивировать вакансию.</i>)",reply_markup=btn_home())

    # Очищаем состояние пользователя
    state_context = await state_for_user(user_id=user_id, chat_id=user_id)
    await state_context.clear()


    admins_data = await action_orm.get_admins_id()

    # удаляем временные данные о посте
    await action_orm.remove_temp_post(temp_post_id)

    # Изменение всех сообщений у админов если кто-то из них ответил на заявку
    for admin_id in  admins_data:
        # получаем объект state администратора
        local_state= await state_for_user(admin_id,admin_id)

        # получаем id сообщения которое нужно изменить
        admin_data=await local_state.get_data()

        # Меняем сообщение
        await callback.bot.edit_message_text(f"{post}\n"
                                             f"\n"
                                             f"Отправитель {username}\n"
                                             f"<b>Пост опубликован!</b>",
                                             chat_id=admin_id,
                                             message_id=admin_data['message_id'],
                                             reply_markup=btn_plug())

        # Сбрасываем состояние для администратора
        await local_state.clear()

    await action_orm.create_new_post(post_text=post,user_id=user_id,message_id=message_id)

    await callback.answer()


@admin_router.callback_query(F.data.regexp(r'admin_delete_\d+$'),AdminState.waiting_action)
async def delete_temp_post(callback: CallbackQuery,state: FSMContext):

    # Получаем нужные данные
    temp_post_id = callback.data.split('_')[-1]  # ID Поста
    temp_data: dict = await action_orm.get_temp_post(temp_post_id)
    post = temp_data['post_text']  # текст поста
    username = temp_data['username']

    admin_data: list[int] = await action_orm.get_admins_id()
    for admin_id in admin_data:

        local_state= await state_for_user(admin_id,admin_id)
        data=await local_state.get_data()
        await callback.bot.edit_message_text(f"{post}\n"
                                             f"\n"
                                             f"Отправитель- {username}\n"
                                             f"<b>Пост удален</b>",
                                             chat_id=admin_id,
                                             message_id=data['message_id'],
                                             reply_markup=btn_plug()
                                             )


    await callback.message.answer('<b>Укажите причину удаления</b>')
    await state.set_state(AdminState.waiting_for_reason)
    await state.update_data(post_id=callback.data.split('_')[-1])



@admin_router.message(AdminState.waiting_for_reason,F.text)
async def remove_temp_post(message:Message, state: FSMContext):
    # Получаем данные поста
    data = await state.get_data()

    post_id = data['post_id']
    reason = message.text
    post_data = await action_orm.get_temp_post(post_id)

    # Удаляем пост из временной базы
    await action_orm.remove_temp_post(post_id)

    # отправляем обратную связь
    await message.bot.send_message(text='<b>Ваш пост не прошел проверку.</b>\n'
                                   '<b>Причина:</b>\n'
                                   f'<i>{reason}</i>',
                                   chat_id=post_data['user_id'],
                                   reply_markup=btn_home())

    # отправляем пользователю в ответ подтверждение
    await message.reply('<b>Пост удален,причина отправлена пользователю</b>')
    state_context = await state_for_user(user_id=post_data['user_id'], chat_id=post_data['user_id'])
    await state_context.clear()

