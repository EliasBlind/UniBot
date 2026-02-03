from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap

def minutes_to_time(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def format_date(timestamp_or_str) -> str:
    if isinstance(timestamp_or_str, (int, float)):
        date_obj = datetime.fromtimestamp(timestamp_or_str)
    elif isinstance(timestamp_or_str, str):
        try:
            date_obj = datetime.fromisoformat(timestamp_or_str)
        except ValueError:
            try:
                date_obj = datetime.strptime(timestamp_or_str, "%Y-%m-%d")
            except ValueError:
                date_obj = datetime.strptime(timestamp_or_str, "%Y-%m-%d %H:%M:%S")
    else:
        date_obj = timestamp_or_str

    weekdays = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }

    weekday_english = date_obj.strftime("%A")
    weekday_russian = weekdays.get(weekday_english, weekday_english)

    return f"{date_obj.strftime('%d.%m.%Y')} ({weekday_russian})"


def generate_schedule_image(schedule_data: list) -> BytesIO:
    if not schedule_data:
        img = Image.new('RGB', (1200, 300), color='#F8F9FA')
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 36)
            font_small = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

        draw.ellipse((500, 50, 700, 250), outline='#6C757D', width=3)
        draw.rectangle((520, 70, 680, 120), fill='#6C757D', outline='#6C757D')
        draw.text((600, 150), "Календарь", fill='#6C757D', font=font, anchor='mm')

        draw.text((600, 230), "Расписание отсутствует",
                  fill='#495057', font=font_small, anchor='mm')

        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes

    days = {}
    for lesson in schedule_data:
        if 'date' in lesson:
            date_value = lesson['date']
            if isinstance(date_value, (int, float)):
                date_str = datetime.fromtimestamp(date_value).strftime('%Y-%m-%d')
            else:
                date_str = str(date_value).split()[0] if ' ' in str(date_value) else str(date_value)
        else:
            continue

        if date_str not in days:
            days[date_str] = []
        days[date_str].append(lesson)

    sorted_days = sorted(days.items())

    HEADER_HEIGHT = 80
    DAY_HEADER_HEIGHT = 70
    LESSON_HEIGHT = 120
    DAY_SPACING = 30
    PADDING = 60
    IMG_WIDTH = 1400
    CARD_RADIUS = 15

    COLORS = {
        'background': '#F8F9FA',
        'header': '#2C3E50',
        'day_header': '#34495E',
        'card_bg': '#FFFFFF',
        'card_shadow': '#E9ECEF',
        'time_badge': '#3498DB',
        'subject_text': '#2C3E50',
        'info_text': '#7F8C8D',
        'border': '#E0E0E0',
        'combine_badge': '#E74C3C',
        'lesson_type_badge': '#2ECC71'
    }

    total_height = PADDING * 2 + HEADER_HEIGHT + 40

    for date_str, lessons in sorted_days:
        total_height += DAY_HEADER_HEIGHT + DAY_SPACING
        total_height += len(lessons) * (LESSON_HEIGHT + 15)

    total_height += 40

    img = Image.new('RGB', (IMG_WIDTH, total_height), color=COLORS['background'])
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 42)
        day_font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 32)
        subject_font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 26)
        time_font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 24)
        info_font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 22)  # Исправлено опечатку
        badge_font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        day_font = ImageFont.load_default()
        subject_font = ImageFont.load_default()
        time_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    header_bg = Image.new('RGBA', (IMG_WIDTH, HEADER_HEIGHT), color=COLORS['header'])
    img.paste(header_bg, (0, 0))

    draw.text((IMG_WIDTH // 2, HEADER_HEIGHT // 2),
              "РАСПИСАНИЕ ЗАНЯТИЙ",
              fill='white', font=title_font, anchor='mm')

    y_position = HEADER_HEIGHT + PADDING

    for date_str, lessons in sorted_days:
        day_title = format_date(date_str)

        draw.rounded_rectangle(
            [PADDING, y_position, IMG_WIDTH - PADDING, y_position + DAY_HEADER_HEIGHT],
            radius=CARD_RADIUS,
            fill=COLORS['day_header'],
            outline=COLORS['day_header']
        )

        day_icon = ""
        draw.text((PADDING + 30, y_position + DAY_HEADER_HEIGHT // 2),
                  day_icon, fill='white', font=day_font, anchor='lm')

        draw.text((PADDING + 80, y_position + DAY_HEADER_HEIGHT // 2),
                  day_title, fill='white', font=day_font, anchor='lm')

        lessons_count = f"{len(lessons)} занятий"
        text_bbox = draw.textbbox((0, 0), lessons_count, font=info_font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text((IMG_WIDTH - PADDING - 30 - text_width, y_position + DAY_HEADER_HEIGHT // 2),
                  lessons_count, fill='white', font=info_font, anchor='lm')

        y_position += DAY_HEADER_HEIGHT + 20

        for i, lesson in enumerate(lessons):
            shadow_offset = 2
            draw.rounded_rectangle(
                [PADDING + shadow_offset, y_position + shadow_offset,
                 IMG_WIDTH - PADDING + shadow_offset, y_position + LESSON_HEIGHT + shadow_offset],
                radius=CARD_RADIUS,
                fill=COLORS['card_shadow'],
                outline=COLORS['card_shadow']
            )

            draw.rounded_rectangle(
                [PADDING, y_position, IMG_WIDTH - PADDING, y_position + LESSON_HEIGHT],
                radius=CARD_RADIUS,
                fill=COLORS['card_bg'],
                outline=COLORS['border'],
                width=2
            )

            time_bg_width = 220
            draw.rounded_rectangle(
                [PADDING + 20, y_position + 20,
                 PADDING + 20 + time_bg_width, y_position + LESSON_HEIGHT - 20],
                radius=10,
                fill=COLORS['time_badge'],
                outline=COLORS['time_badge']
            )

            time_text = f"⏰ {minutes_to_time(lesson['start'])} - {minutes_to_time(lesson['end'])}"
            time_lines = textwrap.wrap(time_text, width=15)
            for j, line in enumerate(time_lines):
                draw.text((PADDING + 20 + time_bg_width // 2,
                           y_position + 40 + j * 30),
                          line, fill='white', font=time_font, anchor='mm')

            subject_x = PADDING + 20 + time_bg_width + 30

            lesson_name = lesson.get('lesson_name', 'Без названия')
            wrapped_subject = textwrap.wrap(lesson_name, width=35)
            for j, line in enumerate(wrapped_subject[:2]):  # Максимум 2 строки
                draw.text((subject_x, y_position + 30 + j * 35),
                          line, fill=COLORS['subject_text'], font=subject_font)

            classroom_y = y_position + 80
            if len(wrapped_subject) > 1:
                classroom_y += 15

            classroom = lesson.get('classroom', 'Не указана')
            classroom_text = f"Аудитория: {classroom}"
            draw.text((subject_x, classroom_y),
                      classroom_text, fill=COLORS['info_text'], font=info_font)

            info_x = IMG_WIDTH - PADDING - 250

            lesson_plan = lesson.get('lesson_plan')
            if lesson_plan:
                plan_text = str(lesson_plan)
                text_bbox = draw.textbbox((0, 0), plan_text, font=badge_font)
                plan_bg_width = text_bbox[2] - text_bbox[0] + 20
                draw.rounded_rectangle(
                    [info_x, y_position + 25, info_x + plan_bg_width, y_position + 55],
                    radius=12,
                    fill=COLORS['lesson_type_badge'],
                    outline=COLORS['lesson_type_badge']
                )
                draw.text((info_x + plan_bg_width // 2, y_position + 40),
                          plan_text, fill='white', font=badge_font, anchor='mm')

            if lesson.get('flag_combine'):
                combine_text = "Объединенная группа"
                text_bbox = draw.textbbox((0, 0), combine_text, font=badge_font)
                text_width = text_bbox[2] - text_bbox[0] + 20

                draw.rounded_rectangle(
                    [info_x, y_position + 65, info_x + text_width, y_position + 95],
                    radius=12,
                    fill=COLORS['combine_badge'],
                    outline=COLORS['combine_badge']
                )
                draw.text((info_x + text_width // 2, y_position + 80),
                          combine_text, fill='white', font=badge_font, anchor='mm')

            y_position += LESSON_HEIGHT + 15

        y_position += DAY_SPACING

    footer_y = total_height - 40
    draw.text((IMG_WIDTH // 2, footer_y),
              f"Всего занятий: {len(schedule_data)} | Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
              fill=COLORS['info_text'], font=info_font, anchor='mm')

    draw.ellipse((100, 100, 300, 300), outline='#E3F2FD', width=1)
    draw.ellipse((150, 150, 250, 250), outline='#F3E5F5', width=1)

    draw.ellipse((IMG_WIDTH - 300, total_height - 300, IMG_WIDTH - 100, total_height - 100),
                 outline='#FFF3E0', width=1)

    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG', optimize=True, quality=95)
    img_bytes.seek(0)

    return img_bytes
