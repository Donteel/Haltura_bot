from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram import F
from Utils.Keyboards import *
from aiogram import Router
from aiogram.filters import Command
from Utils.StateModel import NewPost, DeletePostState
from Utils.config import action_orm, main_chat, application_group
from aiogram.fsm.context import FSMContext
from Utils.functions import get_admins

user_router = Router()


@user_router.message(Command('start'))
async def start(message: Message,state: FSMContext):
    if await state.get_state() == NewPost.pending_confirmation:
        await message.answer('<b>Все действия заблокированы!</b>'
                             '<b>Дождитесь проверки публикации!</b>',reply_markup=btn_standby())
        return
    print(message.chat.id)
    await action_orm.create_user(tg_id=message.from_user.id,
                        username=message.from_user.username)
    await message.reply('Добро пожаловать в Халтура бот,выбери действие.'
                        ,reply_markup=btn_home())


@user_router.message(F.text == '❌ Отменить')
async def start(message: Message,state: FSMContext):
    await state.clear()
    await message.answer('Действие отменено',reply_markup=btn_home())


@user_router.message(Command('help'))
async def start(message: Message):
    await message.reply('Можешь связаться с администратором',
                        reply_markup=btn_links(
                            await get_admins(main_chat,message.bot)
                        )
                        )


@user_router.message(F.text == '📢 Опубликовать готовый пост')
async def create_post(message: Message,state:FSMContext):
    if await state.get_state() == NewPost.pending_confirmation:
        await message.answer('<b>Все действия заблокированы!</b>'
                             '<b>Дождитесь проверки публикации!</b>',reply_markup=btn_standby())
        return
    await message.answer('Пришли мне готовый пост!',reply_markup=btn_cancel())
    await state.set_state(NewPost.awaiting_finished_post)


@user_router.message(F.text == '❌ Закрыть пост')
async def create_post(message: Message,state:FSMContext):
    if await state.get_state() == NewPost.pending_confirmation:
        await message.answer('<b>Все действия заблокированы!</b>'
                             '<b>Дождитесь проверки публикации!</b>',reply_markup=btn_standby())
        return
    await message.answer('Введите ID сообщение полученное при публикации',reply_markup=btn_cancel())
    await state.set_state(DeletePostState.waiting_post_id)


@user_router.message(DeletePostState.waiting_post_id,F.text)
async def delete_post(message: Message,state:FSMContext):
    try:
        post_id = int(message.text)
    except ValueError:
        await message.answer('Нужно отправить номер сообщения без букв,пробелов и любых знаков!')
        return
    else:
        print(message.from_user.id)
        if post_data:= await action_orm.get_post(message_id=post_id,user_id=message.from_user.id):
            print(int(main_chat),int(post_data['message_id']))
            try:
                await message.bot.edit_message_text(text=f"{post_data['post_text']}\n ВАКАНСИЯ ЗАКРЫТА❌",
                                                    chat_id=int(main_chat),
                                                    message_id=int(post_data['message_id'])
                                                    )
                await action_orm.post_deactivate(
                    user_id=int(message.from_user.id),
                    message_id=int(post_data['message_id']
                        )
                )
                await message.answer('Сообщение успешно деактивировано',
                                     reply_markup=btn_home()
                                     )

            except TelegramBadRequest:
                await message.answer('Сообщение уже деактивировано ранее',reply_markup=btn_home())
                await state.clear()

        else:
            await message.answer('Пост с таким номером не был найден',reply_markup=btn_cancel())


@user_router.message(NewPost.awaiting_finished_post)
async def awaiting_post(message: Message,state:FSMContext):
    post = message.text
    post_id = await action_orm.create_temp_post(user_id=message.from_user.id,post_text=post)
    await message.bot.send_message(chat_id=application_group,
                                   text=post,
                                   reply_markup=btn_admin_confirm(post_id))
    await message.answer('Ваш пост отправлен на проверку,ожидайте обновлений',
                         reply_markup=btn_standby()
                         )
    await state.set_state(NewPost.pending_confirmation)





