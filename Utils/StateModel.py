from aiogram.fsm.state import State,StatesGroup

"""
place
📍 Место работы:  
[Укажите место работы]

datatime
⏳ Срочность:  
[Укажите срочность, например: Срочно! / В течение месяца]

job_title
💼 Название вакансии:  
[Укажите название вакансии]

work_schedule
🕒 График работы:  
[Укажите график работы, например: Понед. — Пятн. с 9:00 до 18:00]

task
📋 Задача работника:  
[Укажите основные обязанности]

payment
💸 Оплата:  
[Укажите условия оплаты, например: 100 000 ₽ в месяц, оплата по результатам работы]

contacts
📱 Контакты для связи:  
[Укажите телефон, Telegram или другие контактные данные]
"""

class NewPost(StatesGroup):
    place = State()
    data_time = State()
    job_title = State()
    work_schedule = State()
    task = State()
    payment = State()
    contacts = State()
    awaiting_finished_post = State()
    pending_confirmation = State()

class AdminState(StatesGroup):
    waiting_action = State()
    waiting_for_reason = State()


class DeletePostState(StatesGroup):
    waiting_post_id = State()

