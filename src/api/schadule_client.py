import http.client
import json
import gzip
from datetime import datetime
from typing import List
import logging

import arrow

log = logging.getLogger(__name__)

class Lesson:
    def __init__(self, date: str, sort: int, classroom_id: int, subgroup: int, start: int, end: int,
                 teacher_full: str, teacher_birthday: int, classroom_title: str, subject_title: str, short_subject_title: str):
        self.date = date
        self.sort = sort
        self.classroom_id = classroom_id
        self.subgroup = subgroup
        self.start = start
        self.end = end
        self.teacher_full = teacher_full
        self.teacher_birthday = teacher_birthday
        self.classroom_title = classroom_title
        self.subject_title = subject_title
        self.short_subject_title = short_subject_title

    def __repr__(self):
        return f"Lesson(date={self.date}, sort={self.sort}, subject={self.subject_title})"


def parse_schedule(data: int) -> List[Lesson]:
    log.warning("Created pars data")
    start: int =    int(arrow.get(data).floor('week').timestamp())
    end: int =   int(arrow.get(data).floor('week').shift(days=6).timestamp())
    conn = http.client.HTTPSConnection("api.platform.nke.team:8443")

    payload = ""

    headers = {
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Accept-Language': "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        'Authorization': "Bearer nke",
        'Cache-Control': "no-cache",
        'Connection': "keep-alive",
        'DNT': "1",
        'Origin': "http://www.nke.ru",
        'Pragma': "no-cache",
        'Priority': "u=0",
        'Referer': "http://www.nke.ru/",
        'Sec-Fetch-Dest': "empty",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Site': "cross-site",
        'Sec-GPC': "1",
        'TE': "trailers",
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0"
    }

    conn.request("GET", f"/schedule?start={start}&end={end}&groupId=43", payload, headers)

    res = conn.getresponse()
    data = res.read()

    content_encoding = res.headers.get('Content-Encoding', '')
    if 'gzip' in content_encoding:
        data = gzip.decompress(data)

    json_data = json.loads(data.decode("utf-8"))

    lessons = []
    for item in json_data["items"]:
        date_str = datetime.fromtimestamp(item["date"]).strftime('%Y-%m-%d')
        lesson = Lesson(
            date=date_str,
            sort=item["sort"],
            classroom_id=item["classroomId"],
            subgroup=item["subgroup"],
            start=item["start"],
            end=item["end"],
            teacher_full=item["teacher"]["full"],
            teacher_birthday=item["teacher"]["birthDate"],
            classroom_title=item["classroom"]["title"],
            subject_title=item["plan"]["subject"]["title"],
            short_subject_title=item["plan"]["subject"]["short"]
        )
        lessons.append(lesson)

    lessons.sort(key=lambda x: (x.date, x.sort))
    return lessons