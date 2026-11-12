
#!/usr/bin/env python3
# 今彩539 官方開獎資料讀取程式

import json
import re
import sys

from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser

SOURCE = "https://lotto.ctbcbank.com/result_all.htm"

OUTPUT = Path(__file__).with_name("data539.json")


class TextParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


def read_official():

    req = Request(
        SOURCE,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-TW,zh;q=0.9"
        }
    )

    with urlopen(req, timeout=25) as response:
        raw = response.read()
        charset = (
            response.headers.get_content_charset()
            or "utf-8"
        )

    parser = TextParser()

    parser.feed(
        raw.decode(charset, errors="replace")
    )

    text = " ".join(parser.parts)

    match = re.search(
        r"遊\s*戲\s*今彩\s*539\b",
        text
    )

    if not match:
        raise ValueError(
            "官方網站找不到今彩539資料"
        )

    section = text[
        match.end():match.end() + 3500
    ]

    issue = re.search(
        r"期\s*別\s*第\s*(\d{6,12})\s*期",
        section
    )

    date = re.search(
        r"開獎日期\s*民國\s*(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        section
    )

    numbers = re.search(
        r"依大小順序排列\s*[：:]?\s*((?:\d{1,2}\s+){4}\d{1,2})\b",
        section
    )

    if not all((issue, date, numbers)):
        raise ValueError(
            "無法完整辨識開獎資料"
        )

    vals = [
        int(x)
        for x in numbers.group(1).split()
    ]

    if len(vals) != 5:
        raise ValueError("號碼數量錯誤")

    if len(set(vals)) != 5:
        raise ValueError("號碼重複")

    if any(n < 1 or n > 39 for n in vals):
        raise ValueError("號碼超出範圍")

    year, month, day = map(
        int,
        date.groups()
    )

    draw_date = datetime(
        year + 1911,
        month,
        day
    ).date()

    taiwan_time = timezone(
        timedelta(hours=8)
    )

    if draw_date > datetime.now(taiwan_time).date():
        raise ValueError("開獎日期異常")

    return {
        "game": "今彩539",
        "issue": issue.group(1),
        "draw_date": draw_date.isoformat(),
        "numbers": sorted(vals),
        "source": SOURCE,
        "checked_at": datetime.now(
            taiwan_time
        ).isoformat(timespec="seconds")
    }


def main():

    try:

        result = read_official()

        if OUTPUT.exists():

            previous = json.loads(
                OUTPUT.read_text(
                    encoding="utf-8"
                )
            )

            if previous.get(
                "draw_date", ""
            ) > result["draw_date"]:

                raise ValueError(
                    "新資料比原資料舊"
                )

        OUTPUT.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            ) + "\n",
            encoding="utf-8"
        )

        print("539資料更新成功")

        print("期別：", result["issue"])

        print(
            "日期：",
            result["draw_date"]
        )

        print(
            "號碼：",
            result["numbers"]
        )

    except Exception as exc:

        print(
            "資料讀取失敗：",
            exc,
            file=sys.stderr
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
