import logging
from Utils.config import r, action_orm, gpt_key
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import  InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from Utils.Keyboards import btn_admin_confirm, btn_plug, btn_home
from openai import OpenAI
from Utils.bot_instance import bot
from Utils.config import storage, main_chat



async def state_for_user(user_id: int, chat_id: int) -> FSMContext:
    # Создаём контекст для определённого пользователя
    key = StorageKey(chat_id=chat_id,user_id=user_id,bot_id=7926311537)
    context = FSMContext(storage=storage, key=key)
    return context


async def delete_message(chat_id: int,id_message: int) -> None:

    logging.info(f'Попытка удаления поста номер {id_message} из группы {chat_id}')
    try:
        await bot.delete_message(chat_id,id_message)
    except Exception as e:
        logging.error(f'Произошла ошибка при удалении сообщения\n {e}')
    else:
        logging.info('Пост был успешно удален из группы')


async def clearing_of_all_states(id_data:list[int]):
    for object_id in id_data:
        local_state = await state_for_user(object_id,object_id)
        await local_state.clear()


# функция для публикации сообщения с привлечением HR
async def MessageForHr():

    if r.get('message_id') is not None:

        post_id = int(r.get('message_id').decode('utf-8'))
        logging.info(f'Получен ID старого сообщения - {post_id}')

        await delete_message(chat_id=main_chat,id_message=post_id)

    try:
        logging.info('Попытка отправки нового сообщения в группу')
        message_data = await bot.send_message(
            text='<b>💼 Ищете сотрудников?</b>\n'
                 'Вы можете опубликовать свою вакансию'
                 ' бесплатно через нашего Telegram-бота! 🎯',
            chat_id=int(main_chat),
            reply_markup=
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Опубликовать 🔰',url='t.me/Haltura98_bot')]
            ]
            )
        )
        r.set(name='message_id',value=message_data.message_id)
        logging.info(f"Новый ID сообщения - {message_data.message_id} записан в кеш\n"
                     f"Данные записанные в кэш - {int(r.get('message_id').decode('utf-8'))}")

    except Exception as e:
        logging.error(f'Произошла не предвиденная ошибка при отправке сообщения в группу\n {e}')


async def request_sender(admin_data:list[int],
                         post_text:str,
                         username:str,
                         post_id:int
                         ) -> None:

    """
    Функция для отправления заявки всем администраторам
    :param admin_data: ID администраторов
    :param post_text: текст заявки
    :param username: username отправителя
    :param post_id: ID поста из базы данных
    :return: None
    """
    for admin_id in admin_data:
        logging.info(f'Отправляю сообщение администратору {admin_id}')
        message_obj = await bot.send_message(text=f'📢 <b>Новая вакансия от</b> {username}\n'
                                             f'📝 <b>Текст вакансии:</b>\n'
                                             f'{post_text}\n\n'
                                             f'📌 <b>Статус заявки</b> -  Не обработан.',
                                             chat_id=int(admin_id),
                                             reply_markup=btn_admin_confirm(post_id)
                                             )

        r.set(name=f"{admin_id}_{post_id}",value=message_obj.message_id,ex='7200')
        logging.info(f'Отправлено сообщение администратору {admin_id},'
                     f'добавлена запись в redis ключ - f"{admin_id}_{post_id}", значение {message_obj.message_id}'
                     )


# Рассылка сообщений администраторам
async def admin_broadcast(admin_data:list[int],text:str) -> None:
    admin_count = 0

    for admin_id in admin_data:
        await bot.send_message(chat_id=admin_id,text=text)
        admin_count +=1
    logging.info("Сообщение с текстом:\n"
                 f"{text} отправлено {admin_count} админам")


async def job_posting(post_text:str,chat_id:int,user_id:int) -> int|None:
    try:
        message_obj = await bot.send_message(
            text=f"{post_text}",
            chat_id=int(chat_id)
        )
    except Exception as e:
        logging.info(f"Ошибка публикации в главную группу\n"
                     f"{e}")
        return None
    else:

        await action_orm.create_new_post(post_text=post_text,
                                         user_id=user_id,
                                         message_id=message_obj.message_id
                                         )

        await bot.send_message(
            text='Ваш пост успешно прошел проверку и был выложен в группу.\n'
                 f'Номер публикации - <b><i>{message_obj.message_id}</i></b> он пригодится если вы захотите закрыть вакансию.\n\n'
                 f'<b>Благодарю за использование нашего сервиса!</b>',
            chat_id=int(user_id),
            reply_markup=btn_home()
        )

        return message_obj.message_id


async def post_processing_modification(admins_data,**kwargs):
    """
        Функция изменяет сообщения администраторов если кто-то из них взаимодействовал с заявкой
    """

    post_text = kwargs['post_text']
    post_id = kwargs['id']
    username = kwargs['username']
    key = kwargs['key']
    post_status = 'Опубликован' if key == 'adminconfirm' else 'Удален' # noqa

    for admin_id in admins_data:
        processing_data = r.get(f'{admin_id}_{post_id}')

        print(f'Данные ключа администратора: {processing_data}')

        if processing_data is not None:
            await bot.edit_message_text(text=f'Новая вакансия от @{username}\n'
                                             f'Текст вакансии:\n'
                                             f'{post_text}\n'
                                             f'Статус заявки {post_status}',
                                        chat_id=int(admin_id),
                                        message_id=int(processing_data.decode('utf-8')),
                                        reply_markup=btn_plug()
                                             )
            r.delete(f'{admin_id}_{post_id}')
        else:
            return False
    return True


async def post_moderation(post_text):

    gpt_client = OpenAI(api_key=gpt_key)

    completion = gpt_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role":"system",
             "content":
                 "Ты система которая определяет является ли текст вакансией.\n"
                 "Ты можешь отвечать только числами 0 или 1.\n"
                 "Твоя задача определять является ли текст пользователя вакансией.\n"
                 "Ты проверяешь указаны ли следующие пункты в вакансии:\n"
                 "Обязательно: обязанности, адрес, контактные данные.\n"
                 "Опционально: оплата."
                 "Запрещено: реклама, курьеры, фриланс, регистрации, фин. операции.\n, сомнительные вакансии."
                 "Если текст не относится к вакансии или нарушены правила вакансии ты должен отправить 0 а если все в порядке то 1"
             },
            {"role":"user",
             "content":post_text}
        ]
    )
    logging.info(f'Вакансия - {post_text}\n'
                 f'Вердикт модели - {completion.choices[0].message.content}')

    if completion.choices[0].message.content == "1":
        return True
    else:
        return False

