import hashlib
import os
import uuid

from dotenv import load_dotenv
from yookassa import Configuration, Payment

from utils.config import orm_services

load_dotenv()

shop_id = os.getenv('SHOP_ID')
shop_key = os.getenv('SHOP_KEY')

Configuration.account_id = shop_id
Configuration.secret_key = shop_key



async def create_payment(amount: float,
                         return_url: str,
                         user_id:int,
                         service_id: int,
                         email:str,
                         currency="RUB"):

    service_data = await orm_services.get_service_by_id(service_id)

    payment = Payment.create(
        {
        "amount": {
            "value": f"{float(amount):.2f}",
            "currency": f"{currency}"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"{return_url}"
        },
            "receipt": {
                "customer": {"email": f"{email}"},
                "items": [{
                    "description": f"{service_data.service_name}",
                    "quantity": f"{service_data.quan}",
                    "amount":
                        {
                            "value": f"{float(amount):.2f}",
                            "currency": f"{currency.upper()}"
                        },
                    "vat_code": 1,
                    "payment_subject": "service",
                    "payment_mode": "full_prepayment"
                }]
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


