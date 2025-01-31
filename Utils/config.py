from dotenv import load_dotenv
import os

from redis import Redis

from DataBase.ORM import ActionModel
from aiogram.fsm.storage.redis import RedisStorage

load_dotenv()

storage = RedisStorage.from_url(os.getenv("REDIS_URL"),state_ttl=3600)
bot_token = os.getenv('BOT_TOKEN')
main_chat = os.getenv('CHAT_ID')
application_group = os.getenv('APPLICATION_GROUP')
action_orm = ActionModel()
r = Redis.from_url('redis://localhost:6379/15')
