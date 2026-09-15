import json
import os
import csv
from datetime import datetime

NEWLINE = chr(10)
DATA_DIR = "data"

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_nippo(user_id, nippo_data):
    ensure_data_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR + "/" + user_id[:8] + "_" + timestamp + ".json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(nippo_data, f, ensure_ascii=False, indent=2)
        return filename
    except Exception as e:
        print("Save error: " + str(e))
        return None

def get_monthly_summary(user_id):
    ensure_data_dir()
    prefix = user_id[:8]
    now = datetime.now()
    current_month = now.strftime("%Y%m")
    total_days = 0
    total_workers = 0
    ky_done_count = 0
    ky_total_count = 0
    near_miss_count = 0
    weather_stats = {}
    companies = {}
    files = sorted(os.listdir(DATA_DIR))
    for filename in files:
        if not filename.startswith(prefix):
            continue
        if not filename.endswith(".json"):
            continue
        date_part = filename.split("_")[1] if "_" in filename else ""
        if not date_part.startswith(current_month):
            continue
        filepath = DATA_DIR + "/" + filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        total_days = total_days + 1
        weather = data.get("weather", "")
        if weather:
            weather_stats[weather] = weather_stats.get(weather, 0) + 1
        workers = data.get("workers", [])
        for w in workers:
            total_val = w.get("total", 0)
            try:
                total_val = int(str(total_val))
            except Exception:
                total_val = 0
            total_workers = total_workers + total_val
            company = w.get("company", "不明")
            if company:
                companies[str(company)] = companies.get(str(company), 0) + total_val
        safety = data.get("safety", {})
        if safety:
            ky = safety.get("ky_done", None)
            if ky is not None:
                ky_total_count = ky_total_count + 1
                if ky is True:
                    ky_done_count = ky_done_count + 1
            hh = safety.get("near_miss", None)
            if hh is True:
                near_miss_count = near_miss_count + 1
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
    lines.append("")
    lines.append("【安全管理】")
    if ky_total_count > 0:
        ky_rate = int(ky_done_count / ky_total_count * 100)
        lines.append("KY実施率：" + str(ky_rate) + "%（" + str(ky_done_count) + "/" + str(ky_total_count) + "日）")
    lines.append("ヒヤリハット：" + str(near_miss_count) + "件")
    return NEWLINE.join(lines)