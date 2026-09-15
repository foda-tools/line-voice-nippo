import json
import os
from datetime import datetime

NEWLINE = chr(10)
SPREADSHEET_ID = "1F1BFp7PZ1Q6jyiudxkDLXPHB5Ij5GgM6nVuzgzQ3x28"
SHEET_NAME = "Sheet1"

def get_token():
    try:
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
        from google.oauth2.service_account import Credentials
        from google.auth.transport.requests import Request
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
        creds.refresh(Request())
        return creds.token
    except Exception as e:
        print("Auth error: " + str(e))
        return None

def save_nippo(user_id, nippo_data):
    try:
        import requests as req
        token = get_token()
        if token is None:
            print("Token failed")
            return None
        date_val = str(nippo_data.get("date", ""))
        weather = str(nippo_data.get("weather", ""))
        temp = str(nippo_data.get("temperature", ""))
        workers = nippo_data.get("workers", [])
        rows = []
        if not workers:
            rows.append([date_val, weather, temp, "", "", "", "", "", "", "", ""])
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
                rows.append(row)
        url = "https://sheets.googleapis.com/v4/spreadsheets/" + SPREADSHEET_ID + "/values/" + SHEET_NAME + ":append?valueInputOption=USER_ENTERED"
        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        body = {"values": rows}
        response = req.post(url, headers=headers, json=body)
        if response.status_code == 200:
            print("Saved to sheets!")
            return "saved"
        else:
            print("Sheets error: " + str(response.status_code) + " - " + response.text)
            return None
    except Exception as e:
        print("Save error: " + str(e))
        return None

def get_monthly_summary(user_id):
    try:
        import requests as req
        token = get_token()
        if token is None:
            return "スプレッドシートに接続できませんでした。"
        url = "https://sheets.googleapis.com/v4/spreadsheets/" + SPREADSHEET_ID + "/values/" + SHEET_NAME
        headers = {"Authorization": "Bearer " + token}
        response = req.get(url, headers=headers)
        if response.status_code != 200:
            print("Read error: " + str(response.status_code))
            return "スプレッドシートの読み取りに失敗しました。"
        data = response.json()
        all_rows = data.get("values", [])
        if len(all_rows) <= 1:
            return "今月の日報データがまだありません。音声で日報を送ってください。"
        now = datetime.now()
        current_month = now.strftime("%Y/%m")
        total_workers = 0
        dates_set = set()
        weather_stats = {}
        companies = {}
        zero = int(chr(48))
        one = int(chr(49))
        three = int(chr(51))
        eight = int(chr(56))
        for row in all_rows[one:]:
            if len(row) < (eight + one):
                continue
            date_val = str(row[zero])
            if not date_val.startswith(current_month):
                continue
            dates_set.add(date_val)
            weather = str(row[one]) if len(row) > one else ""
            if weather:
                weather_stats[weather] = weather_stats.get(weather, zero) + one
            total_val = row[eight] if len(row) > eight else "0"
            try:
                total_val = int(str(total_val))
            except Exception:
                total_val = zero
            total_workers = total_workers + total_val
            company = str(row[three]) if len(row) > three else ""
            if company:
                companies[company] = companies.get(company, zero) + total_val
        total_days = len(dates_set)
        if total_days == zero:
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
