from dotenv import load_dotenv
import os
from DataBase.ORM import ActionModel
from aiogram.fsm.storage.redis import RedisStorage

load_dotenv()

storage = RedisStorage.from_url(os.getenv("REDIS_URL"))
bot_token = os.getenv('BOT_TOKEN')
main_chat = os.getenv('CHAT_ID')
application_group = os.getenv('APPLICATION_GROUP')
action_orm = ActionModel()
