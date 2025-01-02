from aiogram.exceptions import TelegramMigrateToChat
from aiogram.types import Message, CallbackQuery
from aiogram import F
from sqlalchemy.testing.plugin.plugin_base import logging
from Utils.Keyboards import *
from aiogram import Router
from Utils.StateModel import AdminState
from Utils.config import action_orm, main_chat
from aiogram.fsm.context import FSMContext
from Utils.functions import state_for_user


admin_router = Router()



@admin_router.callback_query(F.data.regexp(r'admin_confirm_\d+$'))
async def confirm_post(callback: CallbackQuery,state: FSMContext):

    # Получаем нужные данные
    temp_post_id = callback.data.split('_')[-1] # ID Поста
    temp_data: dict = await action_orm.get_temp_post(temp_post_id)
    post = temp_data['post_text'] # текст поста
    user_id = temp_data['user_id'] #user_id поста
    username = temp_data['username']


    try:
        # Отправляем сообщение в канал
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

    await action_orm.remove_temp_post(temp_post_id)

    await callback.bot.edit_message_text(f"{post}\n"
                                         f"\n"
                                         f"Отправитель {username}\n"
                                         f"<b>Пост опубликован!</b>",
                                         chat_id=callback.message.chat.id,
                                         message_id=callback.message.message_id,
                                         reply_markup=btn_plug())
    await action_orm.create_new_post(post_text=post,user_id=user_id,message_id=message_id)
    await callback.answer()


@admin_router.callback_query(F.data.regexp(r'admin_delete_\d+$'))
async def delete_temp_post(callback: CallbackQuery,state: FSMContext):

    # Получаем нужные данные
    temp_post_id = callback.data.split('_')[-1]  # ID Поста
    temp_data: dict = await action_orm.get_temp_post(temp_post_id)
    post = temp_data['post_text']  # текст поста
    username = temp_data['username']


    await callback.bot.edit_message_text(f"{post}\n"
                                         f"\n"
                                         f"Отправитель- {username}\n"
                                         f"<b>Пост удален</b>",
                                         chat_id=callback.message.chat.id,
                                         message_id=callback.message.message_id,
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

