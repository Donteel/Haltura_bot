from aiogram.exceptions import TelegramMigrateToChat
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram import F
from sqlalchemy.testing.plugin.plugin_base import logging
from Utils.Keyboards import *
from aiogram import Router
from Utils.StateModel import AdminState
from Utils.config import action_orm, main_chat,r
from aiogram.fsm.context import FSMContext
from Utils.other import state_for_user, post_processing_modification

admin_router = Router()



@admin_router.callback_query(F.data.regexp(r'adminconfirm_\d+$'))  # noqa
async def confirm_post(callback: CallbackQuery):

    logging.info(f'Администратор {callback.message.chat.id} отозвался на заявку, начинаю обработку')

    post_id = callback.data.split('_')[-1]
    post_data = await action_orm.get_temp_post(post_id)
    post_data['key'] = str(callback.data.split('_')[0])

    logging.info('Попытка обновления информации о заявке у администраторов')
    if await post_processing_modification(**post_data,admins_data=await action_orm.get_admins_id()):
        logging.info('Все сообщения у администраторов успешно изменены на статус обработано')

        message_obj = await callback.bot.send_message(
            text=f"{post_data['post_text']}",
            chat_id=int(main_chat)
        )

        await action_orm.create_new_post(post_text=post_data['post_text'],
                                         user_id=post_data['user_id'],
                                         message_id=message_obj.message_id
                                         )

        await action_orm.remove_temp_post(int(post_id))


        await callback.bot.send_message(text='Ваш пост успешно прошел проверку и был выложен в группу.\n'
                                             f'Номер публикации - <b><i>{message_obj.message_id}</i></b> он пригодится если вы захотите закрыть вакансию.\n\n'
                                             f'<b>Благодарю за использование нашего сервиса!</b>',
                                        chat_id=int(post_data['user_id']),
                                        reply_markup=btn_home()
                                        )
        local_state = await state_for_user(post_data['user_id'],post_data['user_id'])
        await local_state.clear()
    else:
        logging.info('Произошла ошибка изменения сообщений')


@admin_router.callback_query(F.data.regexp(r'admindelete_\d+$'))    # noqa
async def delete_temp_post(callback: CallbackQuery,state: FSMContext):

    post_id = int(callback.data.split('_')[-1])

    post_data = await action_orm.get_temp_post(post_id)

    post_data['key'] = str(callback.data.split('_')[0])
    await post_processing_modification(admins_data=await action_orm.get_admins_id(),
                                       **post_data)
    await callback.message.answer('Пост пользователя будет удален,'
                                  'укажите причину удаления для завершения обработки',
                                  reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdminState.waiting_for_reason)

    await state.update_data(sender_id=post_data['user_id'],post_id=post_id)



@admin_router.message(AdminState.waiting_for_reason,F.text)
async def remove_temp_post(message:Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['sender_id']
    post_id = data['post_id']
    # отправляем сообщение пользователю
    await message.bot.send_message(text='<b>Ваша публикация не прошла проверку</b>\n\n'
                                        f'<b>Причина удаления:</b>\n {message.text}',
                                   chat_id=int(user_id),
                                   reply_markup=btn_home()
                                   )
    # очищаем состояния
    await state.clear()

    local_state = await state_for_user(int(user_id),int(user_id))
    await local_state.clear()
    await action_orm.remove_temp_post(int(post_id))
    logging.info('Пост успешно удален, все данные выгружены')

    await message.answer('Причина отправлена пользователю, все данные удалены!')
