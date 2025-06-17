from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import logging
logging.basicConfig(level=logging.INFO)


def create_reply_keyboard(buttons: tuple,resize_keyboard=True, adjust=1):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(*buttons)
    keyboard.adjust(adjust)
    return keyboard.as_markup(resize_keyboard=resize_keyboard)

def create_inline_keyboard(buttons: tuple | list,adjust: int|list=1):
    keyboard = InlineKeyboardBuilder()
    for button in buttons:
        keyboard.row(*button)
    return keyboard.as_markup()


def btn_home():

    btn_1 = KeyboardButton(text='📤 Отправить готовую')
    btn_2 = KeyboardButton(text='📝 Создать вручную')
    btn_3 = KeyboardButton(text='❌ Закрыть вакансию')
    btn_4 = KeyboardButton(text='📜 Правила')

    return create_reply_keyboard((btn_1, btn_2, btn_3, btn_4))


def btn_admins(links: list[str:str]):
    """
    :param links: list содержит кортежи (ссылка/administrator)
    :return: inline клавиатуру
    """

    return create_inline_keyboard(
        [[InlineKeyboardButton(text=f'{name}',url=f't.me/{link}')] for link, name in links]
    )


def btn_confirm():

    btn_1 = KeyboardButton(text='✅ Подтвердить')
    btn_2 = KeyboardButton(text='🔄 Создать заново')

    return create_reply_keyboard((btn_1, btn_2),adjust=2)


def btn_cancel_create():

    btn_1 = KeyboardButton(text='❌ Отменить создание')

    return create_reply_keyboard((btn_1,))


def btn_cancel():

    btn_1 = KeyboardButton(text='❌ Отменить')

    return create_reply_keyboard((btn_1,))


def btn_approval(post_id):

    btn_1 = InlineKeyboardButton(text="Пропустить 📤", callback_data=f"adminConfirm_{post_id}")
    btn_2 = InlineKeyboardButton(text="Удалить 🗑️",callback_data=f"adminDelete_{post_id}")
    btn_3 = InlineKeyboardButton(text="⛔ удалить и Блок",callback_data=f'delAndBlock_{post_id}')

    return create_inline_keyboard([[btn_1, btn_2],[btn_3]])


def btn_plug(verdict):

    btn_1 = InlineKeyboardButton(text=f'{verdict}',callback_data="plug")

    return create_inline_keyboard([[btn_1],])


def btn_standby():

    btn_1 = KeyboardButton(text='Ожидайте подтверждение')

    return create_reply_keyboard((btn_1,))

def btn_link(button_text: str, rules_link: str):

    btn_1 = InlineKeyboardButton(text=f'{button_text}', url=rules_link)

    return create_inline_keyboard(
        [
            [btn_1]
        ]
    )

def btn_subscribe():
    btn_1= InlineKeyboardButton(text='Подписаться 👀',url='https://t.me/+gtQppDLgOT0xYWMy')
    btn_2= InlineKeyboardButton(text='Проверить 👮🏻‍♂️', callback_data='subscribe')

    return create_inline_keyboard([[btn_1],[btn_2]])

def btn_rules(rules_link: str):

    btn_1 = InlineKeyboardButton(text='Читать...', url=rules_link)

    return create_inline_keyboard([[btn_1]])


def btn_moderation(temp_id):
    btn_1 = InlineKeyboardButton(text="❌ Отменить", callback_data=f'postingCancel_{temp_id}')
    btn_2 = InlineKeyboardButton(text="⛔ Отмена и Блок", callback_data=f'cancelAndBlock_{temp_id}')

    return create_inline_keyboard([[btn_1,btn_2]])

def btn_limit_act(recipient_id,value=0):

    btn_1 = InlineKeyboardButton(text="➕",callback_data=f"counter:{value+1}:{recipient_id}")
    btn_2 = InlineKeyboardButton(text=f"{value}",callback_data=f"none_data")
    btn_3 = InlineKeyboardButton(text="➖", callback_data=f"counter:{value-1}:{recipient_id}")
    btn_4 = InlineKeyboardButton(text="🚀 Выполнить", callback_data=f"add_limits:{recipient_id}:{value}")

    return create_inline_keyboard(
        [
            [btn_1,btn_2,btn_3],
            [btn_4]
        ]
    )
