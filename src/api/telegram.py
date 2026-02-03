import telebot
import logging
from datetime import datetime, timedelta

import src.config.token
import src.app.image.app as image_gen
import src.api.ai as ai
from app.schedule.app import Schedule
from config.config import Config

log = logging.getLogger(__name__)


class TGBot:
    def __init__(self, cfg: Config, schedule: Schedule):
        self.cfg = cfg
        self.schedule = schedule
        self.bot = telebot.TeleBot(src.config.token.TOKEN)

        self.register_handlers()

    def register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome_wrapper(message):
            self.send_welcome(message)

        @self.bot.message_handler(commands=['schedule'])
        def send_schedule_wrapper(message):
            self.send_schedule_image(message)

        @self.bot.message_handler(commands=['thinking_ai'])
        def ai_handler_wrapper(message):
            self.ai_handler(message)

        @self.bot.message_handler(content_types=['text'])
        def ai_response_wrapper(message):
            self.ai_response(message)

    def send_welcome(self, message):
        welcome_text = """
    <b>Добро пожаловать в бот расписания!</b>

    <b>Доступные команды:</b>
    /schedule - Получить расписание на текущую неделю
    /thinking_ai - Использовать более продвинутую нейросеть
    <b>Особенности:</b>
    • Автоматическое обновление расписания
    • Красивое оформление в виде изображения
    • Информация о времени, аудиториях и типах занятий

    Для начала работы просто нажмите /schedule
        """
        self.bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')

    def send_schedule_image(self, message):
        try:
            today = datetime.now().date()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

            log.info(f"Get {start_date} {end_date}")

            schedule_data = self.schedule.get()
            log.info(f"Get {len(schedule_data) if schedule_data else 0}")

            if not schedule_data:
                self.bot.send_message(message.chat.id,
                                      "На эту неделю расписание не найдено.\n\n"
                                      "Возможно, занятия еще не добавлены или вы выбрали не учебную неделю.",
                                      parse_mode='HTML')
                return

            if schedule_data:
                sample_lesson = schedule_data[0]
                log.info(f"lessons: {list(sample_lesson.keys())}")

            img_bytes = image_gen.generate_schedule_image(schedule_data)

            caption = f"""
    📅 <b>Расписание занятий</b>
    🗓️ Период: {start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m.%Y')}
    👥 Всего занятий: {len(schedule_data)}
    ⏰ Время генерации: {datetime.now().strftime('%H:%M')}

    <i>Для обновления расписания используйте команду /schedule</i>
            """

            self.bot.send_photo(message.chat.id, img_bytes,
                                caption=caption,
                                parse_mode='HTML')

            log.info(f"Send schedule {message.from_user.id}")

        except Exception as e:
            log.error(f"Error gen: {str(e)}", exc_info=True)
            self.bot.reply_to(message,
                              "❌ Произошла ошибка при генерации расписания.\n"
                              "Попробуйте позже или обратитесь к администратору.")

    def ai_handler(self, message):
        try:
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                self.bot.reply_to(message, "Пожалуйста, напишите ваш вопрос после команды /thinking_ai")
                return

            user_query = command_parts[1]
            response = ai.thinking_request(user_query)
            log.info(f"Question: {user_query}, Request: {response}")
            self.bot.reply_to(message, response)

        except Exception as e:
            log.error(f"Error ai request: {str(e)}", exc_info=True)
            self.bot.reply_to(message, "Произошла ошибка при обработке запроса. Попробуйте позже.")

    def ai_response(self, message):
        if message.text.startswith('/'):
            return

        try:
            response = ai.thinking_request(message.text)
            log.info(f"Question: {message.text}, Request: {response}")
            self.bot.reply_to(message, response)
        except Exception as e:
            log.error(f"Error ai request: {str(e)}", exc_info=True)
            self.bot.reply_to(message, "Произошла ошибка при обработке запроса. Попробуйте позже.")

    def start(self):
        log.info("Bot started")
        self.bot.infinity_polling()
        return self

    def stop(self):
        try:
            self.bot.stop_polling()
        except AttributeError:
            log.warning("Bot already stopped")

        log.info("Bot stop")