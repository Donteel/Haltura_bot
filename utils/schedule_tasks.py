from apscheduler.triggers.cron import CronTrigger
from utils.other import channel_message
from utils.config import scheduler
import zoneinfo

time_zone = zoneinfo.ZoneInfo('Europe/Moscow')

# Публикация рекламы бота
scheduler.add_job(
    channel_message,
    CronTrigger(hour='8,17', timezone=time_zone),
    args=('<b>💼 Ищете сотрудников?</b>\n'
          'Вы можете опубликовать свою вакансию'
          ' бесплатно через нашего Telegram-бота! 🎯',
          )
)