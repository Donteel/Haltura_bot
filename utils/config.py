from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
from redis import Redis
from openai import OpenAI


from DataBase.base_model import MessageModel
from DataBase.crud import UserManagementBase, PostManagementBase, MessageManagementBase
from aiogram.fsm.storage.redis import RedisStorage

load_dotenv()

storage = RedisStorage.from_url(os.getenv("REDIS_URL"),state_ttl=3600)
bot_token = os.getenv('BOT_TOKEN')
gpt_key = os.getenv('AI_API_KEY')
main_chat = os.getenv('CHANNEL_ID')
application_group = os.getenv('APPLICATION_GROUP')
action_orm = UserManagementBase()
orm_posts = PostManagementBase()
orm_messages = MessageManagementBase()
r = Redis.from_url('redis://localhost:6379/15')

job_stories = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db'),
}

executor = {
    'default': ThreadPoolExecutor(max_workers=10)
}
scheduler = AsyncIOScheduler(job_stories=job_stories, executor=executor)