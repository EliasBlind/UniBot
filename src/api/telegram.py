import telebot
import logging
from datetime import datetime, timedelta

import src.config.token
from app.schedule.app import Schedule
from src.config.config import Config
import src.logger.logger as logger
import src.app.image.app as image_gen
import src.api.ai as ai

cfg = Config()
logger.configure(cfg)
log = logging.getLogger(__name__)
schedule = Schedule(cfg)

bot = telebot.TeleBot(src.config.token.TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
 <b>Добро пожаловать в бот расписания!</b>

<b>Доступные команды:</b>
/schedule - Получить расписание на текущую неделю
/thinking_ai - Использовать более продвинутую нееросеть
<b>Особенности:</b>
• Автоматическое обновление расписания
• Красивое оформление в виде изображения
• Информация о времени, аудиториях и типах занятий

Для начала работы просто нажмите /schedule
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')


@bot.message_handler(commands=['schedule'])
def send_schedule_image(message):
    try:
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

        log.info(f"Get {start_date} {end_date}")

        schedule_data = schedule.get()
        log.info(f"Get {len(schedule_data) if schedule_data else 0}")

        if not schedule_data:
            bot.send_message(message.chat.id,
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

        bot.send_photo(message.chat.id, img_bytes,
                       caption=caption,
                       parse_mode='HTML')

        log.info(f"Send schedule {message.from_user.id}")

    except Exception as e:
        log.error(f"Error gen: {str(e)}", exc_info=True)
        bot.reply_to(message,
                     "❌ Произошла ошибка при генерации расписания.\n"
                     "Попробуйте позже или обратитесь к администратору.")


@bot.message_handler(commands=['thinking_ai'])
def ai_handler(message):
    try:
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) < 2:
            bot.reply_to(message, "Пожалуйста, напишите ваш вопрос после команды /ai")
            return

        user_query = command_parts[1]

        response = ai.thinking_request(user_query)
        log.info(f"Question: {user_query}, Request: {response}")
        bot.reply_to(message, response)

    except Exception as e:
        log.error(f"Error ai request: {str(e)}", exc_info=True)
        bot.reply_to(message, "Произошла ошибка при обработке запроса. Попробуйте позже.")

@bot.message_handler(content_types=['text'])
def ai_response(message):
    try:
        response = ai.thinking_request(message.text)
        log.info(f"Question: {message.text}, Request: {response}")
        bot.reply_to(message, response)
    except Exception as e:
        log.error(f"Error ai request: {str(e)}", exc_info=True)
        bot.reply_to(message, "Произошла ошибка при обработке запроса. Попробуйте позже.")

log.info("Bot started")
bot.infinity_polling()