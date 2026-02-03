import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Optional

from api.schadule_client import Lesson
from src.app.db.shedule import ScheduleDb
import src.api.schadule_client as schedule_client
import src.config.config as config
import logging

log: logging.Logger = logging.getLogger(__name__)


class Schedule:
    def __init__(self, cfg: config.Config):
        self.cfg = cfg
        self.data = ScheduleDb(cfg)
        self.need_update = datetime.now() + timedelta(minutes=self.cfg.schedule_update)
        log.info("Schedule class initialized")

    def get(self):
        if self.need_update < datetime.now():
            new_lessons = schedule_client.parse_schedule(int(time.time()))
            self.data.update_schedule(new_lessons)
            self.need_update = datetime.now() + timedelta(minutes=self.cfg.schedule_update + random.randint(0, 30))
        return self.data.get_schedule(int(time.time()))
