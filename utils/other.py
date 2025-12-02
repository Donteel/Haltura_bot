import logging
from aiogram.exceptions import TelegramBadRequest
from aiogram import Bot
from utils.bot_instance import bot
from aiogram.fsm.state import State
from apscheduler.jobstores.base import JobLookupError
from database.objects.message_object import MessageObject
from utils.config import r, action_orm, gpt_key,scheduler, orm_posts, orm_messages, storage, main_chat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.keyboards import btn_plug, btn_home, btn_moderation
from openai import OpenAI




# Создаём контекст для определённого пользователя
async def state_for_user(user_id) -> FSMContext:
    key = StorageKey(chat_id=user_id,user_id=user_id,bot_id=7926311537)
    context = FSMContext(storage=storage, key=key)
    return context


# устанавливает состояние для указанного пользователя
async def set_state_for(id_list:list,state_class: State):
    for user_id in id_list:
        state = await state_for_user(user_id)
        await state.set_state(state_class)


# удаляет сообщение из чата/канала/группы
async def delete_message(chat_id: int,id_message: int) -> None:

    logging.info(f'Попытка удаления поста номер {id_message} из группы {chat_id}')
    try:
        await bot.delete_message(chat_id,id_message)
    except Exception as e:
        logging.error(f'Произошла ошибка при удалении сообщения\n {e}')
    else:
        logging.info('Пост был успешно удален из группы')


# функция для публикации регулярного сообщения
async def channel_message(message_text):

    if r.get('message_id') is not None:

        post_id = int(r.get('message_id').decode('utf-8'))
        logging.info(f'Получен ID старого сообщения - {post_id}')

        await delete_message(chat_id=main_chat,id_message=post_id)

    try:
        logging.info('Попытка отправки нового сообщения в группу')
        message_data = await bot.send_message(
            text=message_text,
            chat_id=int(main_chat),
            reply_markup=
                InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Опубликовать 🔰',url='t.me/Haltura98_bot')] # noqa
                    ]
                )
        )

        r.set(name='message_id',value=message_data.message_id)

        logging.info(f"Новый ID сообщения - {message_data.message_id} записан в кеш\n"
                     
                     f"Данные записанные в кэш - {int(r.get('message_id').decode('utf-8'))}")

    except Exception as e:
        logging.error(f'Произошла не предвиденная ошибка при отправке сообщения в группу\n {e}')


# Функция для отправления заявки всем администраторам
async def request_sender(admin_data:list[int],post_id: int) -> None:

    """
    Функция для отправления заявки всем администраторам
    :param admin_data: ID администраторов
    :param post_id: id записи в бд
    :return: None
    """

    post = await orm_posts.get_post(post_id)

    logging.info(f"По ID {post_id} был получен объект вакансии:"
                 f"Id - {post.id}\n"
                 f"UserID - {post.user_id}\n"
                 f"UserName{post.username}\n"
                 f"message_id - {post.message_id}")

    logging.info("Начинаю рассылку по администраторам")
    for admin in admin_data:

        # отправка сообщения админам
        message_obj = await bot.send_message(
            chat_id=admin,
            text="Новая вакансия от пользователя!\n"
                 "<b>Будет опубликована через 5 минут.</b>\n\n"
                 "<u>Текст вакансии:</u>\n"
                 f"{post.post_text}\n\n"
                 f"<u>Отправитель - @{post.username}</u>",
            reply_markup= btn_moderation(post.id)
        )


        # сохранить данные отправленных заявок для возможного изменения

        admin_message = MessageObject(admin_id=admin,
                                      post_id=post.id,
                                      message_id=message_obj.message_id
                                      )
        logging.info("Сообщение администратору отправлено:"
                     f"ID сообщения {message_obj.message_id}\n"
                     f"PostID {post.id}"
                     )


        await orm_messages.add_message_data(admin_message)



# Функция рассылки сообщения администраторам
async def admin_broadcast(admin_data:list[int],text:str,keyboard=btn_home) -> None:
    """
    Рассылка сообщения администраторам

    :param admin_data: список ID администраторов
    :param text: текст сообщения
    :param keyboard: клавиатура
    :return: None
    """
    admin_count = 0

    for admin_id in admin_data:
        await bot.send_message(chat_id=admin_id,text=text,reply_markup=keyboard())
        admin_count +=1
    logging.info("Сообщение с текстом:\n"
                 f"{text} отправлено {admin_count} админам")


# Публикует пост в группу
async def post_publication(chat_id:int,post_id) -> None:
    """
    Публикует пост в группу
    :param chat_id: id группы
    :param post_id: id записи о вакансии
    :return: None
    """
    post_data = await orm_posts.get_post(post_id)
    user_data = await action_orm.get_user(int(post_data.user_id))
    try:
        # отправляем вакансию в канал
        message_obj = await bot.send_message(
            text=f"{post_data.post_text}\n\n"
                 f"📆 В системе с: {user_data.created_at.strftime("%d.%m.%Y")}",
            chat_id=int(chat_id)
        )

    except Exception as e:
        logging.info(f"Ошибка публикации в  группу\n"
                     f"{e}")
        return None
    else:

        # создаем запись в базу данных
        await orm_posts.addMessageId_to_post(post_id=post_data.id,
                                              message_id=message_obj.message_id
                                              )


        await bot.send_message(
            text='<b>Пост успешно выложен в группу.</b>\n'
                 f'Номер публикации - <code><i>{message_obj.message_id}</i></code> он пригодится для закрытия вакансии.\n\n'
                 f'<b>Благодарим за использование нашего сервиса!</b>',
            chat_id=int(post_data.user_id),
            reply_markup=btn_home()
        )

        return message_obj.message_id


# Функция изменяет сообщение у администраторов
# на конкретный пост в зависимости от вердикта администратора.
async def change_admin_message(admins_data:list,post_id: int,verdict: str) -> None:
    """
    Функция изменяет сообщение у администраторов
     на конкретный пост в зависимости от вердикта администратора.

    :param admins_data: Список id администраторов
    :param post_id: id записи в бд
    :param verdict: вердикт администратора
    :return: bool
    """
    verdicts = {"adminConfirm":"Опубликовано",
                "adminDelete":"Удалено",
                "postCancel":"Отменено",
                "cancelAndBlock":"Отменён и Блокирован",
                "delAndBlock": "Удален и Блокирован"
                }

    for admin in admins_data:

        ms_obj = await orm_messages.get_message(admin,int(post_id))

        verdict_text = verdicts[verdict]

        await bot.edit_message_reply_markup(
            chat_id=admin,
            message_id=ms_obj.message_id,
            reply_markup=btn_plug(f"{verdict_text}!")
        )


# проверка статуса пользователя в группе/канале
async def check_member_status(bot_obj: Bot,user_id: int, group_id: int) -> bool:
    try:

        member = await bot_obj.get_chat_member(group_id,user_id)
        print(member.status)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramBadRequest as e:
        logging.error('При проверке пользователя на подписку произошла ошибка,'
                      ' неверный ID группы или пользователь не подписан'
                      f'{e.__dict__}')
        return False


# AI модерация вакансий
async def post_moderation(post_text):

    gpt_client = OpenAI(api_key=gpt_key)
    try:
        completion = gpt_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system",
                 "content":
                     "Ты система которая определяет является ли текст вакансией.\n"
                     "Твоя задача определять является ли текст пользователя вакансией.\n"
                     "Ты проверяешь указаны ли следующие пункты в вакансии:\n"
                     "Обязательно: "
                     "обязанности: что нужно делать или вид деятельности, "
                     "адрес: указание адреса, места встречи или метро, "
                     "контактные данные: номер телефона, телеграм или любые другие,\n"
                     "оплата: указание часовой ставки,месячной или цены за рабочий день\n\n"
                     "Запрещено:\n"
                     " реклама,\n"
                     "вакансии предполагающие получение бонусов за привлечение новых сотрудников или клиентов"
                     " (курьерские службы, такси, доставка еды, каршеринг, интернет-магазины и прочие сервисы"
                     " с реферальными программами),\n"
                     "фриланс(любые онлайн работы),\n"
                     " регистрации, фин. операции.\n,"
                     "сомнительные вакансии(завуалированные вакансии наркошопов, обнал и другие серые/черные схемы)"
                     "Если текст не относится к вакансии или нарушены правила вакансии ты должен отправить"
                     " коротко причину по которой пост не проходит а если все в порядке то одно слово pass"
                     "Будь мягче к людям с  реальными хорошими вакансиями и строг к запрещенным видам вакансий."
                 },
                {"role":"user",
                 "content":post_text}
            ]
        )
        logging.info(f'Вакансия - {post_text}\n'
                     f'Вердикт модели - {completion.choices[0].message.content}')

        return completion.choices[0].message.content

    except Exception as e:
        await admin_broadcast(await action_orm.get_admins_id(),
                              "Бот получил ошибку из за которой не смог проверить вакансию.\n"
                                    f"Текст ошибки:\n {e}"
                              )
        return "Произошла ошибка обработки. код model-error"

# функция отмены задачи
def schedule_cancel(schedule_id):
    try:
        scheduler.remove_job(schedule_id)
    except JobLookupError as e:
        logging.error(f"Произошла ошибка остановки задачи № {schedule_id}\n"
                      f"{e}")
        return False
    except Exception as e:

        logging.error("Произошла непредвиденная ошибка удаления задачи\n"
                      f"{e}")
        return False
    return True

# проверка лимитов
def check_limit_publication(post_count: int,limit=2):
    if post_count >= limit:
        return False
    return True

# async def limit_calculation(deposit,price):
#     result : float = deposit / price
#     return int(result)
