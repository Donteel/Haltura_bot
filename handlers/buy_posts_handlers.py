from aiogram.types import Message, CallbackQuery
from aiogram import F
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from utils.config import orm_services, orm_payments
from utils.keyboards import btn_pay_methods, btn_link
from utils.state_models import PaymentState
from web_server.payments import create_payment

buy_posts_router = Router()


@buy_posts_router.callback_query(F.data.startswith("service:"),PaymentState.payment_state)
async def service_handler(callback: CallbackQuery, state: FSMContext):

    # клиент нажал на кнопку с определенной услугой
    # получаем данные об услуге

    callback_data,service_id = callback.data.split(":")

    state_data = await state.get_data()

    user_email = state_data["email"]

    service = await orm_services.get_service_by_id(service_id)

    await state.update_data(
        service_id=service.id,
        quantity=service.quan,
        user_id=callback.from_user.id
    )

    # даем информацию об услуге клиенту и просим выбрать количество единиц товара

    payment_methods: list[tuple] = await orm_payments.get_payment_methods()

    await callback.bot.edit_message_text(
        f'<b>Услуга:</b> {service.service_name}\n'
            f'<b>Стоимость:</b> {service.service_price}\n'
            f'<b>Email:</b> {user_email}'
            f'\n'
            f'Выберите способ оплаты:',
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=btn_pay_methods(payment_methods
                                     )
    )




@buy_posts_router.callback_query(F.data == 'yookassa', PaymentState.payment_state)
async def pay_freekassa_handler(callback: CallbackQuery, state: FSMContext):

    user_data = await state.get_data()
    service = await orm_services.get_service_by_id(user_data['service_id'])
    state_data = await state.get_data()
    user_email = state_data["email"]

    amount_data = {
        "amount":f"{service.service_price}",
        "return_url":"https://t.me/Haltura98_bot",
        "user_id":f"{callback.from_user.id}",
        "email":f"{user_email}",
        "currency":"RUB",
        "service_id":f"{service.id}"
    }

    await callback.bot.edit_message_text(
        'После оплаты вы получите уведомление от бота.',
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=btn_link(
            "Оплатить",
            await create_payment(**amount_data)
        )
    )




