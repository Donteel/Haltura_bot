import logging

from fastapi import FastAPI, Request

from aiogram.types import ReplyKeyboardRemove
from utils.bot_instance import bot
from utils.config import orm_services, action_orm
from utils.currency_dict import CUR_ID_MAP
from utils.other import admin_broadcast

app = FastAPI()


# метод получения уведомления об оплате
@app.post("/payment/yookassa/webhook")
async def payment_complete(request: Request):

    data = await request.json()

    event = data.get("event")
    obj = data.get("object", {})

    metadata = data["object"].get("metadata", {})
    user_id = metadata.get("user_id")
    service_id = metadata.get("service_id")

    payment_id = obj.get("id")
    status = obj.get("status")
    amount = obj.get("amount", {}).get("value")
    currency = obj.get("amount", {}).get("currency")
    description = obj.get("description")
    created_at = obj.get("created_at")
    expires_at = obj.get("expires_at")
    payment_method_type = obj.get("payment_method", {}).get("type")
    card_last4 = obj.get("payment_method", {}).get("card", {}).get("last4")

    logging.info(f"Сервер получил уведомление {event}")



    text_for_admins = (f"<b>[тип уведомления] - {event}</b>\n"
                       f"<b>[статус платежа] -</b> {status}\n"
                       f"[Номер заказа] - {payment_id}\n"
                       f"[Сумма пополнения] - {amount} {currency}\n"
                       )

    match event:
        case "payment.waiting_for_capture":
            pass
        case "payment.succeeded":

            service = await orm_services.get_service_by_id(int(service_id))


            await action_orm.change_extra_limit(
                user_id=int(user_id),
                action="plus",
                limit=int(service.quan)
            )

            text_for_user = \
                f"✅ Платёж успешно проведён!\n\n" \
                f"💳 Сумма: {amount} {currency}\n" \
                f"🧾 Номер заказа: {payment_id}\n" \
                f"Получено: {service.quan} лимитов\n\n" \
                f"Спасибо за покупку!"

            await bot.send_message(chat_id=int(user_id),
                                   text=text_for_user)
        case "payment.canceled":

            await bot.send_message(chat_id=int(user_id),
                                   text="Ваш платеж отклонен!")

    await admin_broadcast(
        admin_data=await action_orm.get_admins_id(),
        text=text_for_admins,
        keyboard=ReplyKeyboardRemove
    )