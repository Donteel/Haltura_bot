from dotenv import load_dotenv
import os
from aiogram.fsm.storage.redis import RedisStorage
load_dotenv()

storage = RedisStorage.from_url(os.getenv("REDIS_URL"))
bot_token = os.getenv('BOT_TOKEN')

