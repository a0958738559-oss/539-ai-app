
import csv
import io
import re
import urllib.request
from datetime import date
from html.parser import HTMLParser

URL = "https://lotto2.arclink.com.tw/results/history/tw539/chart.html"
OUTPUT = "539_data.csv"


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def main():
    req = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")

    parser = TableParser()
    parser.feed(html)

    records = []
    year = date.today().year
    month = None
    previous_month = None

    for row in parser.rows:
        values = [x.strip() for x in row if x.strip()]

        if not values or "星期" in values:
            continue

        if len(values) == 9:
            month_text, day_text = values[0], values[1]
            nums = values[4:9]
        elif len(values) == 8:
            month_text, day_text = values[0], values[1]
            nums = values[3:8]
        elif len(values) == 7 and month is not None:
            month_text, day_text = str(month), values[0]
            nums = values[2:7]
        else:
            continue

        try:
            new_month = int(month_text)
            day = int(day_text)
            numbers = [int(x) for x in nums]

            if previous_month == 12 and new_month == 1:
                year += 1

            month = new_month
            previous_month = month

            draw_date = date(year, month, day)

            if draw_date > date.today():
                continue

            if len(numbers) != 5:
                continue

            if len(set(numbers)) != 5:
                continue

            if not all(1 <= n <= 39 for n in numbers):
                continue

            records.append([
                draw_date.isoformat(),
                "",
                *[f"{n:02d}" for n in numbers]
            ])

        except (ValueError, TypeError):
            continue

    if not records:
        raise RuntimeError("沒有取得有效開獎資料，停止更新。")

    records.sort(key=lambda x: x[0])

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "date", "period",
        "n1", "n2", "n3", "n4", "n5"
    ])
    writer.writerows(records)

    with open(OUTPUT, "w", encoding="utf-8-sig", newline="") as f:
        f.write(buffer.getvalue())

    print(f"已取得 {len(records)} 筆資料")
    print(f"最新資料日期：{records[-1][0]}")


if __name__ == "__main__":
    main()
