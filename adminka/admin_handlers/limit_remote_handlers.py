import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from utils.bot_instance import bot
from utils.config import action_orm
from utils.keyboards import btn_cancel, btn_limit_act, btn_home
from utils.state_models import AdminState

limit_router = Router()


@limit_router.message(Command('add_limit'))
async def add_limit_for_user(message: Message, state: FSMContext):
    if message.from_user.id in await action_orm.get_admins_id():
        await message.answer("Введи id пользователя.",
                             reply_markup=btn_cancel()
                             )
        await state.set_state(AdminState.add_limit_state)

@limit_router.message(~F.text.regexp(r"\d+"), AdminState.add_limit_state)
async def add_user_post_limit(message: Message):
    await message.reply("Формат указан неправильно, повторите." ,reply_markup=btn_cancel())


@limit_router.message(F.text.regexp(r"\d+"), AdminState.add_limit_state)
async def add_user_post_limit(message: Message ,state: FSMContext):

    if await action_orm.get_user(int(message.text)):

        await message.answer(
            "Укажи количество публикаций.",
            reply_markup=btn_limit_act(
                recipient_id=int(message.text)
            )
        )

        await state.set_state(AdminState.awaiting_action_for_limit)
    else:
        await message.answer("Пользователь не найден, отправь правильный ID",
                             reply_markup=btn_cancel()
                             )


@limit_router.callback_query(F.data.startswith("counter:"),AdminState.awaiting_action_for_limit)
async def action_menu(callback: CallbackQuery, state:FSMContext):


    value = int(callback.data.split(":")[1])
    user_id = int(callback.data.split(":")[2])
    user_limit = await action_orm.get_extra_limit(user_id)

    if ( user_limit + value) < 0:
        await callback.answer('баланс пользователя меньше указанного значения!',show_alert=True)
        return


    await callback.message.edit_reply_markup(
        reply_markup=btn_limit_act(
            recipient_id=user_id,
            value=int(value)
        )
    )
    await callback.answer()


@limit_router.callback_query(F.data.startswith("add_limits:"),AdminState.awaiting_action_for_limit)
async def finalization_of_limits(callback: CallbackQuery, state: FSMContext):
    callback_text,\
    user_id,\
    value_of_limits = callback.data.split(":")

    if value_of_limits == "0":
        await callback.message.answer(
            "Ты должен прибавить или убавить хоть одну публикацию!",
            reply_markup=btn_limit_act(
                int(user_id)
            )
        )

    try:
        await action_orm.change_extra_limit(user_id=int(user_id),
                                            action="plus",
                                            limit=int(value_of_limits)
                                            )

    except Exception as e:

        logging.error("Произошла ошибка добавления платных лимитов пользователю",
                      e.__dict__
                      )
        await callback.message.answer("Произошла непредвиденная ошибка!",reply_markup=btn_home())
        await state.clear()
    else:
        arg_for_msg = "добавил" if int(value_of_limits) > 0 else "убавил"

        await bot.send_message(
            text=f"<b>Администратор {arg_for_msg} вам "
                 f"лимиты для публикаций в количестве: "
                 f"{value_of_limits if int(value_of_limits) > 0 else abs(int(value_of_limits))} </b>",
            chat_id=int(user_id)
        )

        await callback.message.edit_text(
            "<b>Действие успешно завершено.</b>\n"
            "Пользователь получил уведомление.\n\n"
            f"Выдано публикаций: {value_of_limits}"
        )

    await callback.answer()