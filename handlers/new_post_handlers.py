from aiogram.types import Message
from aiogram import F
from handlers.user_handlers import awaiting_post
from middlewares.add_user_middleware import AddUserMiddleware
from middlewares.blacklist_middlewares import CheckBlackListMiddleWare
from middlewares.subscription_verification import SubscriptionVerificationMiddleware
from utils.config import action_orm
from utils.keyboards import *
from aiogram import Router
from utils.state_models import NewPost
from aiogram.fsm.context import FSMContext
from utils.other import request_sender, post_moderation


create_post_router = Router()


create_post_router.message.middleware(CheckBlackListMiddleWare())
create_post_router.callback_query.middleware(CheckBlackListMiddleWare())
create_post_router.message.middleware(AddUserMiddleware())
create_post_router.callback_query.middleware(AddUserMiddleware())
create_post_router.message.middleware(SubscriptionVerificationMiddleware())
create_post_router.callback_query.middleware(SubscriptionVerificationMiddleware())


@create_post_router.message(~F.text)
async def type_message_error(message: Message):
    await message.answer('Я понимаю только текст!')


@create_post_router.message(F.text == '❌ Отменить создание')
async def cancel_create(message: Message,state: FSMContext):
    await state.clear()
    await message.answer('Создание отменено',reply_markup=btn_home())


@create_post_router.message(F.text == "📝 Создать вручную")
async def start_creating(message: Message,state: FSMContext):
    user_id = message.chat.id
    daily_limit: int = await action_orm.get_user_limit(user_id)
    extra_limit: int = await action_orm.get_extra_limit(user_id)

    logging.info("лимиты пользователя:\n"
                 f"Ежедневных - {daily_limit}\n"
                 f"Экстра - {extra_limit}"
                 )

    if daily_limit + extra_limit > 0:
        await message.answer(
            f'📄 [<i>Доступно публикаций: {daily_limit+extra_limit}</i>]\n\n'
            f'🏢 <b>Начнем создание вакансии.!</b>\n'
            'Где предстоит работать? (название компании или локация к месту работы)',
            reply_markup=btn_cancel_create()
        )
        await state.set_state(NewPost.company_name)
    else:
        await message.answer(
            "😊 <b>У вас закончились публикации.</b> \n"
            "Вы можете докупить <i>лимиты</i> по команде /buy_limits \n\n",
            reply_markup=btn_home()
        )
        await state.clear()

@create_post_router.message(NewPost.company_name)
async def waiting_name_company(message: Message,state:FSMContext):

    await state.update_data(company_name=message.text)
    await message.answer('📍 Укажите город и район.')
    await state.set_state(NewPost.place)


# Место работы
@create_post_router.message(NewPost.place)
async def awaiting_place(message: Message,state: FSMContext):
    await state.update_data(place=message.text)
    await message.answer('⏳ Когда нужно приступить: немедленно, в течение недели или в удобное время?')
    await state.set_state(NewPost.data_time)


# Начало работы
@create_post_router.message(NewPost.data_time)
async def awaiting_datatime(message: Message,state: FSMContext):
    await state.update_data(datatime=message.text)
    await message.answer('💼 Укажите должность или формат работы.')
    await state.set_state(NewPost.job_title)


# Название вакансии
@create_post_router.message(NewPost.job_title)
async def awaiting_job_title(message: Message,state: FSMContext):
    await state.update_data(job_title=message.text)
    await message.answer('🕒 Какой режим работы?\n'
                         'Укажите часы работы и график смен,или объем работы в количестве часов.')
    await state.set_state(NewPost.work_schedule)

# График работы
@create_post_router.message(NewPost.work_schedule)
async def awaiting_work_schedule(message: Message,state: FSMContext):
    await state.update_data(work_schedule=message.text)
    await message.answer('📋 Что именно нужно делать?')
    await state.set_state(NewPost.task)

# Задачи работника
@create_post_router.message(NewPost.task)
async def awaiting_task(message: Message,state: FSMContext):
    await state.update_data(task=message.text)
    await message.answer('💸 Какая сумма и форма оплаты? (почасовая, за смену, за весь заказ)')
    await state.set_state(NewPost.payment)

# Оплата
@create_post_router.message(NewPost.payment)
async def awaiting_payment(message: Message,state: FSMContext):
    await state.update_data(payment=message.text)
    await message.answer('Последний шаг!\n\n'
                         '📱 Телефон, Telegram, WhatsApp или другой удобный способ.')
    await state.set_state(NewPost.contacts)

# Связь
@create_post_router.message(NewPost.contacts)
async def awaiting_contacts(message: Message,state: FSMContext):
    await state.update_data(contacts=message.text)
    data  = await state.get_data()

    new_post =  f"📍 <b>Локация:</b>\n"\
                f"{data['place']}\n"\
                "\n"\
                f"🏢 <b>Компания / Работодатель:</b>\n"\
                f"{data['company_name']}\n"\
                "\n"\
                f"⏳ <b>Срочность:</b>\n"\
                f"{data['datatime']}\n"\
                "\n"\
                f"💼 <b>Должность / Вид работы</b>\n"\
                f"{data['job_title']}\n"\
                "\n"\
                f"🕒 <b>График работы:</b>\n"\
                f"{data['work_schedule']}\n"\
                "\n"\
                f"📋 <b>Обязанности:</b>\n"\
                f"{data['task']}\n"\
                "\n"\
                f"💸 <b>Зарплата:</b>\n"\
                f"{data['payment']}\n"\
                "\n"\
                f"📱 <b>Контакты для связи:</b>\n"\
                f"{data['contacts']}"

    await state.update_data(post_text=new_post)

    await message.answer(new_post)

    await message.answer('Устраивает пост?',reply_markup=btn_confirm())

    await state.set_state(NewPost.pending_confirmation)

# Подтверждение оплаты
@create_post_router.message(NewPost.pending_confirmation,F.text == "✅ Подтвердить")
async def awaiting_pending_confirmation(message: Message,state: FSMContext):

    await awaiting_post(message,state)



# создание поста заново
@create_post_router.message(NewPost.pending_confirmation,F.text == "🔄 Создать заново")
async def reload_constructor(message: Message,state: FSMContext):

    await state.clear()
    await start_creating(message,state)
