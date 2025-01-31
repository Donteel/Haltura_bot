from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import logging
logging.basicConfig(level=logging.INFO)


def btn_home():
    keyboard = ReplyKeyboardBuilder()
    btn_1 = KeyboardButton(text='📢 Опубликовать готовый пост')
    btn_2 = KeyboardButton(text='📝 Создать пост по шаблону')
    btn_3 = KeyboardButton(text='❌ Закрыть пост')
    btn_4 = KeyboardButton(text='📜 Правила')


    keyboard.add(btn_1, btn_2, btn_3, btn_4)

    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)

def btn_links(links:list[str:str]):
    """
    :param links: list содержит кортежи (ссылка/administrator)
    :return: inline клавиатуру
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.add(*[InlineKeyboardButton(text=f'⛑ {name}',url=f't.me/{link}') for link, name in links])
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)


def btn_confirm():
    keyboard = ReplyKeyboardBuilder()
    btn_1 = KeyboardButton(text='✅ Подтвердить')
    btn_2 = KeyboardButton(text='🔄 Создать заново')
    keyboard.add(btn_1, btn_2)
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)

def btn_cancel_create():
    keyboard = ReplyKeyboardBuilder()
    btn_1 = KeyboardButton(text='❌ Отменить создание')
    keyboard.add(btn_1)
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)

def btn_cancel():
    keyboard = ReplyKeyboardBuilder()
    btn_1 = KeyboardButton(text='❌ Отменить')
    keyboard.add(btn_1)
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)


def btn_admin_confirm(post_id):
    keyboard = InlineKeyboardBuilder()

    btn_1 = InlineKeyboardButton(text="Пропустить 📤", callback_data=f"adminconfirm_{post_id}") # noqa
    btn_2 = InlineKeyboardButton(text="Удалить 🗑️",callback_data=f"admindelete_{post_id}") # noqa

    keyboard.add(btn_1, btn_2)
    keyboard.adjust(2)

    return keyboard.as_markup()

def btn_plug():
    keyboard = InlineKeyboardBuilder()
    btn_1 = InlineKeyboardButton(text='Пост обработан',callback_data="plug")
    keyboard.add(btn_1)
    keyboard.adjust(1)
    return keyboard.as_markup()

def btn_standby():
    keyboard = ReplyKeyboardBuilder()
    btn_1 = KeyboardButton(text='Ожидайте подтверждение')
    keyboard.add(btn_1)
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)


def btn_rules(rules_link: str):
    keyboard = InlineKeyboardBuilder()
    btn_1 = InlineKeyboardButton(text='Читать...', url=rules_link)
    keyboard.add(btn_1)
    keyboard.adjust(1)
    return keyboard.as_markup()
