import hashlib
import os
import uuid

from dotenv import load_dotenv
from yookassa import Configuration, Payment

load_dotenv()

shop_id = os.getenv('SHOP_ID')
shop_key = os.getenv('SHOP_KEY')

Configuration.account_id = shop_id
Configuration.secret_key = shop_key



def create_payment(amount, return_url, user_id, service_id, currency="RUB"):
    payment = Payment.create(
        {
        "amount": {
            "value": f"{amount}",
            "currency": f"{currency}"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"{return_url}"
        },
        "capture": True,
        "description": f"Покупка публикаций в телеграм-канале: Вакансии | СПБ 🧡 ",
        "metadata": {
            "user_id": user_id,
            "service_id": service_id,
        }
    }, uuid.uuid4())

    result = payment.confirmation
    return result.confirmation_url


