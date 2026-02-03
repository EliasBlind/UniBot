from api.telegram import TGBot
from config.config import Config
from src.app.schedule.app import Schedule
import src.logger.logger as logger
import signal

class App:
    def __init__(self):
        self.cfg = Config()
        logger.configure(self.cfg)
        self.schedule = Schedule(self.cfg)
        self.tg_bot = TGBot(self.cfg, self.schedule).start()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    @staticmethod
    def _signal_handler(self):
        self.tg_bot.stop()
        self.stop()