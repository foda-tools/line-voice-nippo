import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

NEWLINE = chr(10)
SPREADSHEET_ID = "1F1BFp7PZ1Q6jyiudxkDLXPHB5Ij5GgM6nVuzgzQ3x28"

def get_sheet():
    creds_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json")
    if not os.path.exists(creds_file):
        creds_json = os.environ.get("GOOGLE_CREDENTIALS", "")
        if creds_json:
            creds_file = "/tmp/credentials.json"
            with open(creds_file, "w") as f:
                f.write(creds_json)
        else:
            print("No credentials found")
            return None
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

def save_nippo(user_id, nippo_data):
    try:
        sheet = get_sheet()
        if sheet is None:
            print("Sheet connection failed")
            return None
        date_val = str(nippo_data.get("date", ""))
        weather = str(nippo_data.get("weather", ""))
        temp = str(nippo_data.get("temperature", ""))
        workers = nippo_data.get("workers", [])
        if not workers:
            row = [date_val, weather, temp, "", "", "", "", "", "", "", ""]
            sheet.append_row(row)
        else:
            for w in workers:
                row = [
                    date_val,
                    weather,
                    temp,
                    str(w.get("company", "")),
                    str(w.get("job_type", "")),
                    str(w.get("foreman", "")),
                    str(w.get("skilled", "")),
                    str(w.get("apprentice", "")),
                    str(w.get("total", "")),
                    str(w.get("work_category", "")),
                    str(w.get("description", ""))
                ]
                sheet.append_row(row)
        return "saved"
    except Exception as e:
        print("Save error: " + str(e))
        return None

def get_monthly_summary(user_id):
    try:
        sheet = get_sheet()
        if sheet is None:
            return "スプレッドシートに接続できませんでした。"
        all_data = sheet.get_all_records()
        if not all_data:
            return "今月の日報データがまだありません。音声で日報を送ってください。"
        now = datetime.now()
        current_month = now.strftime("%Y/%m")
        total_workers = 0
        dates_set = set()
        weather_stats = {}
        companies = {}
        ky_done_count = 0
        ky_total_count = 0
        for row in all_data:
            date_val = str(row.get("日付", ""))
            if not date_val.startswith(current_month):
                continue
            dates_set.add(date_val)
            weather = str(row.get("天候", ""))
            if weather:
                weather_stats[weather] = weather_stats.get(weather, 0) + 1
            total_val = row.get("合計人工", 0)
            try:
                total_val = int(str(total_val))
            except Exception:
                total_val = 0
            total_workers = total_workers + total_val
            company = str(row.get("会社名", ""))
            if company:
                companies[company] = companies.get(company, 0) + total_val
        total_days = len(dates_set)
        if total_days == 0:
            return "今月の日報データがまだありません。音声で日報を送ってください。"
        lines = []
        lines.append("--- " + now.strftime("%Y年%m月") + " 月次サマリー ---")
        lines.append("")
        lines.append("稼働日数：" + str(total_days) + "日")
        lines.append("累計人工：" + str(total_workers) + "人工")
        lines.append("")
        lines.append("【天候統計】")
        for w_name, w_count in weather_stats.items():
            lines.append("・" + str(w_name) + "：" + str(w_count) + "日")
        lines.append("")
        lines.append("【会社別人工】")
        sorted_companies = sorted(companies.items(), key=lambda x: x, reverse=True)
        for c_name, c_total in sorted_companies:
            lines.append("・" + str(c_name) + "：" + str(c_total) + "人工")
        return NEWLINE.join(lines)
    except Exception as e:
        print("Summary error: " + str(e))
        return "集計エラーが発生しました。もう一度お試しください。"