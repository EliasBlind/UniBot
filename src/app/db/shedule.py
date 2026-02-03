import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Any

import logging
import arrow

import src.config.config as config
from src.api.schadule_client import Lesson

log: logging.Logger = logging.getLogger(__name__)

class ScheduleDb:
    def __init__(self, cfg: config.Config):
        self.cfg = cfg
        self.db_name: str = cfg.db_name
        self.DB_PATH = Path(cfg.storage_path)
        self.db_init()
        log.info("data base init")

    def update_schedule(self, lessons: list[Lesson]):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedule")
            conn.commit()
        except Exception as e:
            log.error(f"Error removed lessons all: {e}")
        finally:
            if conn:
                conn.close()
        for lesson in lessons:
            subgroup = False if lesson.subgroup is None else True
            self.add_lesson_in_schedule(
                lesson_name=lesson.subject_title,
                classroom_id=lesson.classroom_id,
                classroom=lesson.classroom_title,
                lesson_plan=lesson.sort,
                start=lesson.start,
                end=lesson.end,
                data=lesson.date,
                flag_combine=subgroup
            )

    def lessons_in_day(self, dates: set[str]) -> dict[str, list[Lesson]]:
        conn = None
        lessons_by_date: dict[str, list[Lesson]] = {}

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            placeholders = ','.join(['?' for _ in dates])
            query = f"""
                SELECT 
                    l.name as lesson_name,
                    l.short as lesson_name_short,
                    s.id_classroom,
                    s.classroom,
                    s.lesson_plan,
                    s.start,
                    s.end,
                    s.date,
                    s.flag_combine,
                    t.name as teacher_name,
                    t.birthday as teacher_birthday
                FROM schedule s
                JOIN lesson l ON s.id_lesson = l.id
                JOIN teacher t ON t.id = l.id_teacher
                WHERE s.date IN ({placeholders})
                ORDER BY s.date, s.start
            """

            cursor.execute(query, tuple(dates))
            db_lessons = [dict(row) for row in cursor.fetchall()]

            for db_lesson in db_lessons:
                date = db_lesson["date"]
                lesson = Lesson(
                    date=date,
                    sort=db_lesson["lesson_plan"],
                    classroom_id=db_lesson["id_classroom"],
                    classroom_title=db_lesson["classroom"],
                    subgroup=db_lesson["flag_combine"],
                    start=db_lesson["start"],
                    end=db_lesson["end"],
                    teacher_full=db_lesson["teacher_name"],
                    teacher_birthday=db_lesson["teacher_birthday"],
                    subject_title=db_lesson["lesson_name"],
                    short_subject_title=db_lesson["lesson_name_short"]
                )

                if date not in lessons_by_date:
                    lessons_by_date[date] = []
                lessons_by_date[date].append(lesson)

        except Exception as e:
            log.error(f"Error get lessons {e}")
            return {}
        finally:
            if conn:
                conn.close()

        return lessons_by_date

    @staticmethod
    def _are_lessons_equal(old_lessons: list[Lesson], new_lessons: list[Lesson]) -> bool:
        if len(old_lessons) != len(new_lessons):
            return False

        old_sorted = sorted(old_lessons, key=lambda x: (x.start, x.end, x.subject_title))
        new_sorted = sorted(new_lessons, key=lambda x: (x.start, x.end, x.subject_title))

        for old_lesson, new_lesson in zip(old_sorted, new_sorted):
            if (old_lesson.subject_title != new_lesson.subject_title or
                    old_lesson.teacher_full != new_lesson.teacher_full or
                    old_lesson.classroom_title != new_lesson.classroom_title or
                    old_lesson.start != new_lesson.start or
                    old_lesson.end != new_lesson.end or
                    old_lesson.subgroup != new_lesson.subgroup):
                return False

        return True

    def _remove_lessons_by_date(self, date: str) -> None:
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedule WHERE date = ?", (date,))
            conn.commit()
        except Exception as e:
            log.error(f"Error removed lessons on the date: {date}, {e} ")
        finally:
            if conn:
                conn.close()

    def add_cascade(self, lessons: List[Lesson]):
        log.info("Starting cascade add lessons in db")
        lessons_name = self.get_lessons_name()
        for lesson in lessons:
            log.info(f"lessons adding: {lesson}")
            if lesson.subject_title not in lessons_name:
                log.warning(f"lesson {lesson.subject_title} not founded in db")
                lessons_name.append(lesson.subject_title)
                self.add_teacher(lesson.teacher_full, lesson.teacher_birthday)
                self.add_lesson(lesson.teacher_full, lesson.subject_title, lesson.short_subject_title)

            flag_combine = False
            if lesson.subgroup is not None:
                log.info(f"in {lesson.subject_title} will combined lesson")
                flag_combine = True
            self.add_lesson_in_schedule(
                lesson.subject_title,
                lesson.classroom_id,
                lesson.classroom_title,
                lesson.sort,
                lesson.start,
                lesson.end,
                lesson.date,
                flag_combine
            )

    def remove_lesson_in_schedule(self, id: int):
        conn = None
        log.info(f"Remove lesson witch id: {id}")
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM schedule WHERE id = ?
            """, (id,))
            conn.commit()
        except Exception as e:
            log.error(f"Error deleted lesson in table schedule {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        log.info("Creating connection")
        conn = sqlite3.connect(self.DB_PATH/self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def db_init(self) -> None:
        log.info(f"Starting init db: {self.DB_PATH/self.db_name}")
        conn = None
        try:
            self.DB_PATH.mkdir(parents=True, exist_ok=True)
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS teacher (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    birthday INTEGER
                );

                CREATE TABLE IF NOT EXISTS lesson (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_teacher INTEGER NOT NULL,
                    name TEXT UNIQUE NOT NULL,
                    short TEXT,
                    FOREIGN KEY (id_teacher) REFERENCES teacher(id)
                );

                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_lesson INTEGER NOT NULL,
                    id_classroom INTEGER NOT NULL,
                    classroom TEXT NOT NULL,
                    lesson_plan INTEGER NOT NULL,
                    start INTEGER NOT NULL,
                    end INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    flag_combine BOOL DEFAULT 0,
                    FOREIGN KEY (id_lesson) REFERENCES lesson(id)
                );
            """)
            conn.commit()
            log.info("Data base created")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in cursor.fetchall()]
            log.info(f"Created tables: {tables}")
        except Exception as e:
            log.error(f"Error init DB: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def add_lesson(self, teacher_name: str, lesson_name: str, short: str | None) -> None:
        conn = None
        log.info(f"Add new lesson {lesson_name}")
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM teacher WHERE name = ?", (teacher_name,))
            result = cursor.fetchone()
            if not result:
                log.warning(f"Teacher {teacher_name} not found")
                raise ValueError(f"Teacher {teacher_name} not found")
            teacher_id = result[0]

            cursor.execute(
                "INSERT INTO lesson (id_teacher, name, short) VALUES (?, ?, ?)",
                (teacher_id, lesson_name, short)
            )
            conn.commit()
        except Exception as e:
            log.error(f"Error adding new lesson: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()


    def add_teacher(self, name: str, birthday: int | None = None) -> None:
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """INSERT OR IGNORE INTO teacher (name, birthday) 
                   VALUES (?, ?)""",
                (name, birthday)
            )
            log.info(f"Add new teacher: {name} witch birthday in {birthday}")
            conn.commit()
        except Exception as e:
            log.error(f"Error added new teacher: {e}")
            conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
            log.info("New teacher added")

    def add_lesson_in_schedule(self, lesson_name: str, classroom_id: int, classroom: str, lesson_plan: int, start: int, end: int, data: str, flag_combine: bool) -> None:
        conn = None
        try:
            log.info(f"add new lesson {lesson_name} in schedule")
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                " SELECT id FROM lesson WHERE name = ? ",  (lesson_name,)
            )
            result = cursor.fetchone()
            if not result:
                log.warning(f"Lesson {lesson_name} not found")
                raise ValueError(f"Lesson {lesson_name} not found")
            lesson_id: int = result[0]
            cursor.execute("""INSERT OR IGNORE INTO schedule 
                              (id_lesson, id_classroom, classroom, lesson_plan, 
                               start, end, date, flag_combine) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                           (lesson_id, classroom_id, classroom, lesson_plan,
                            start, end, data, flag_combine))
            conn.commit()
        except Exception as e:
            log.error(f"Error added new lesson in schedule: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

    def get_schedule(self, data: int):
        conn = None
        try:
            gmt7 = timezone(timedelta(hours=7))

            start: int = int(arrow.get(data).floor('week').timestamp())
            end: int =  int(arrow.get(data).floor('week').shift(days=6).timestamp())
            log.info(f"unix time start: {start}, end: {end}")
            log.info(f"Start reading schedule from db start date: {start}, end date: {end}")
            start = datetime.fromtimestamp(start, tz=gmt7)
            end = datetime.fromtimestamp(end, tz=gmt7)

            conn = self.get_connection()
            cursor = conn.cursor()
            log.info(f"iso start: {start}, end: {end}")
            cursor.execute(
                """
                SELECT 
                    s.id,
                    l.name as lesson_name,
                    s.id_classroom,
                    s.classroom,
                    s.lesson_plan,
                    s.start,
                    s.end,
                    s.date,
                    s.flag_combine
                FROM schedule s
                JOIN lesson l ON s.id_lesson = l.id
                WHERE s.date BETWEEN ? AND ?
                ORDER BY s.date, s.start
                """, (start, end)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            if conn:
                conn.close()

    def get_teacher_name(self) -> list[str]:
        conn = None
        log.info("Reading all teachers name")
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM teacher
            """)
            return [row[0] for row in cursor.fetchall()]
        finally:
            if conn:
                conn.close()

    def get_lessons_name(self) -> list[str]:
        log.info("Reading all lessons name")
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM lesson
            """)
            return [row[0] for row in cursor.fetchall()]
        finally:
            if conn:
                conn.close()