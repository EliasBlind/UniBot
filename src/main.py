import asyncio
import time
import logging

from config.config import Config
from src.app.schedule.app import Schedule
import src.logger.logger as logger

def main():
    cfg = Config()
    logger.configure(cfg)
    log = logging.getLogger(__name__)
    log.info(f"Reading config: {cfg}")

    log.info("Initializing schedule")
    schedule = Schedule(cfg)
    print(schedule.get())


if __name__ == "__main__":
    main()