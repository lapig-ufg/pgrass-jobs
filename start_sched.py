import sched
import time
from datetime import datetime, timedelta
from app.config import logger, settings
from start_job import start

scheduler = sched.scheduler(timefunc=time.time)

def reschedule():
    new_target = datetime.now().replace(second=0, microsecond=0)
    new_target += timedelta(minutes=settings.SCHEDULER_TIME)
    logger.info(f'Next scan scheduled for {new_target}')
    scheduler.enterabs(new_target.timestamp(),
                       priority=0,
                       action=sched_run)

def sched_run():
    start()
    reschedule()


reschedule()
scheduler.run(blocking=True)


