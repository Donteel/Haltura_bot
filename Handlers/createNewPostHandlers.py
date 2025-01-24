from aiogram.types import Message
from aiogram import F
from Utils.Keyboards import *
from aiogram import Router
from Utils.StateModel import NewPost, AdminState
from Utils.config import action_orm, main_chat, application_group
from aiogram.fsm.context import FSMContext

from Utils.other import state_for_user, request_sender

create_post_router = Router()

@create_post_router.message(~F.text)
async def type_message_error(message: Message):
    await message.answer('Я понимаю только текст!')


@create_post_router.message(F.text == '❌ Отменить создание')
async def cancel_create(message: Message,state: FSMContext):
    await state.clear()
    await message.answer('Создание отменено',reply_markup=btn_home())


@create_post_router.message(F.text == "📝 Создать пост по шаблону")
async def start_creating(message: Message,state: FSMContext):
    await message.answer('<b>Начнем создание поста!</b>\n'
                        '<i>Укажите место работы.</i>', reply_markup=btn_cancel_create())
    await state.set_state(NewPost.place)


# Место работы
@create_post_router.message(NewPost.place)
async def awaiting_place(message: Message,state: FSMContext):
    await state.update_data(place=message.text)
    await message.answer('<i>Укажите срочность, например: Завтра</i>')
    await state.set_state(NewPost.data_time)


# Начало работы
@create_post_router.message(NewPost.data_time)
async def awaiting_datatime(message: Message,state: FSMContext):
    await state.update_data(datatime=message.text)
    await message.answer('<i>Укажите название вакансии.</i>')
    await state.set_state(NewPost.job_title)


# Название вакансии
@create_post_router.message(NewPost.job_title)
async def awaiting_job_title(message: Message,state: FSMContext):
    await state.update_data(job_title=message.text)
    await message.answer('Укажите график работы, например: Понед. — Пятн. с 9:00 до 18:00.')
    await state.set_state(NewPost.work_schedule)

# График работы
@create_post_router.message(NewPost.work_schedule)
async def awaiting_work_schedule(message: Message,state: FSMContext):
    await state.update_data(work_schedule=message.text)
    await message.answer('Опишите основные обязанности работника.')
    await state.set_state(NewPost.task)

# Задачи работника
@create_post_router.message(NewPost.task)
async def awaiting_task(message: Message,state: FSMContext):
    await state.update_data(task=message.text)
    await message.answer('<i>Укажите условия оплаты.\n'
                         'Например: 100 000 ₽ в месяц или 5000₽ в день </i>]')
    await state.set_state(NewPost.payment)

# Оплата
@create_post_router.message(NewPost.payment)
async def awaiting_payment(message: Message,state: FSMContext):
    await state.update_data(payment=message.text)
    await message.answer('Последний шаг!,Укажите телефон, Telegram или другие контактные данные для связи')
    await state.set_state(NewPost.contacts)

# Связь
@create_post_router.message(NewPost.contacts)
async def awaiting_contacts(message: Message,state: FSMContext):
    await state.update_data(contacts=message.text)
    data  = await state.get_data()

    new_post = f"📍 <b>Место работы:</b>\n<i>{data['place']}</i>\n"\
                         f"\n"\
                         f"⏳ <b>Срочность:</b>\n<i>{data['datatime']}</i>\n"\
                         f"\n"\
                         f"💼 <b>Название вакансии:</b>\n<i>{data['job_title']}</i>\n"\
                         f"\n"\
                         f"🕒 <b>График работы:</b>\n<i>{data['work_schedule']}</i>\n"\
                         f"\n"\
                         f"📋 <b>Задача работника:</b>\n<i>{data['task']}</i>\n"\
                         f"\n"\
                         f"💸 <b>Оплата:</b>\n<i>{data['payment']}</i>\n"\
                         f"\n"\
                         f"📱 <b>Контакты для связи:</b>\n<i>{data['contacts']}</i>"
    await state.update_data(post=new_post)
    await message.answer(new_post)

    await message.answer('Устраивает пост?',reply_markup=btn_confirm())

    await state.set_state(NewPost.pending_confirmation)

# Подтверждение оплаты
@create_post_router.message(NewPost.pending_confirmation,F.text == "✅ Подтвердить")
async def awaiting_pending_confirmation(message: Message,state: FSMContext):
    data = await state.get_data()
    admin_data: list[int] = await action_orm.get_admins_id()

    if post_id := await action_orm.create_temp_post(post_text=data['post'],
                                                    user_id=message.from_user.id,
                                                    username=message.from_user.username):
        await request_sender(
            admin_data=admin_data,
            post_text=data['post'],
            username=message.from_user.username,
            post_id=post_id
        )

        await message.answer('Ваш пост отправлен на проверку,ожидайте обновлений',
                             reply_markup=btn_standby()
                             )


# создание поста заново
@create_post_router.message(NewPost.pending_confirmation,F.text == "🔄 Создать заново")
async def awaiting_pending_confirmation(message: Message,state: FSMContext):
    await state.clear()
    await start_creating(message,state)
