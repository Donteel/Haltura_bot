from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from Utils.other import MessageForHr
import zoneinfo

time_zone = zoneinfo.ZoneInfo('Europe/Moscow')


job_stories = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db'),
}

executor = {
    'default': ThreadPoolExecutor(max_workers=10)
}

scheduler = AsyncIOScheduler(job_stories=job_stories, executor=executor)


# Задача для публикации сообщения о возможности публиковать сообщения с помощью бота
scheduler.add_job(MessageForHr, CronTrigger(hour='8,17',timezone=time_zone))

# scheduler.add_job(MessageForHr, CronTrigger(minute='28,29',timezone=time_zone))