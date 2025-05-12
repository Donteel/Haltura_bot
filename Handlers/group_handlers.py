# import logging
#
# from aiogram import Router, F
# from aiogram.types import Message
#
# group_router = Router()
#
# @group_router.message(F.left_chat_member)
# async def group_handler(message: Message):
#     logging.info(f"Пользователь {message.from_user.id} вышел из группы")
#
#
#
# @group_router.message(F.new_chat_members)
# async def group_handler(message: Message):
#     logging.info(f"Пользователь {message.from_user.id} добавился в группу")