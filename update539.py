
"""更新今彩539歷史資料。來源不可用時不覆寫既有 CSV。"""
import csv
import io
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

URL = "https://lotto2.arclink.com.tw/results/history/tw539/chart.html"
OUTPUT = Path(__file__).with_name("539_data.csv")
TODAY = datetime.now(ZoneInfo("Asia/Taipei")).date()


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


def fetch_html():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; 539DataUpdater/1.0)",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.5",
        },
    )
    print("正在讀取：", URL, flush=True)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            print("最終網址：", response.geturl(), flush=True)
            content_type = response.headers.get_content_type()
            if content_type not in ("text/html", "application/xhtml+xml"):
                raise RuntimeError(f"回傳內容不是網頁：{content_type}")
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        print(f"HTTP 錯誤：{exc.code} {exc.reason}", file=sys.stderr)
        print("重新導向位置 Location：", exc.headers.get("Location", "(未提供)"), file=sys.stderr)
        if exc.code in (301, 302, 303, 307, 308):
            print("來源網站要求重新導向，可能限制 GitHub Actions 存取。請確認 Location 與來源站規則。", file=sys.stderr)
        raise
    except urllib.error.URLError as exc:
        print(f"網路連線失敗：{exc.reason}", file=sys.stderr)
        raise


def extract_records(html):
    parser = TableParser()
    parser.feed(html)
    records = []
    year = TODAY.year
    month = None
    previous_month = None
    for row in parser.rows:
        values = [x.strip() for x in row if x.strip()]
        if not values or "星期" in values:
            continue
        if len(values) >= 9:
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
            elif previous_month == 1 and new_month == 12:
                year -= 1
            month = new_month
            previous_month = month
            draw_date = date(year, month, day)
            if draw_date > TODAY or len(numbers) != 5:
                continue
            if len(set(numbers)) != 5 or not all(1 <= n <= 39 for n in numbers):
                continue
            records.append((draw_date.isoformat(), "", *[f"{n:02d}" for n in numbers]))
        except (ValueError, TypeError):
            continue
    return sorted(set(records), key=lambda x: x[0])


def main():
    html = fetch_html()
    records = extract_records(html)
    if not records:
        raise RuntimeError("未取得有效539資料，停止更新；既有檔案保持不變。網站版型可能已變更。")
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "period", "n1", "n2", "n3", "n4", "n5"])
    writer.writerows(records)
    # 先確認資料有效，才覆寫檔案。
    OUTPUT.write_text(buffer.getvalue(), encoding="utf-8-sig")
    print(f"已取得 {len(records)} 筆資料")
    print(f"最新資料日期：{records[-1][0]}")
    print("注意：來源未提供可核驗期別時，period 欄位保持空白。")


if __name__ == "__main__":
    main()
