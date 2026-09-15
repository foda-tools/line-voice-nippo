import json
import requests
from config import OPENAI_API_KEY

NEWLINE = chr(10)

def convert_to_nippo(transcribed_text):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + OPENAI_API_KEY
    }

    system_prompt = """あなたは建設現場の日報作成アシスタントです。
現場監督の音声テキストを解析し、日報データに変換してください。

以下のJSON形式で出力してください。不明な項目はnullにしてください。

{
  "date": "今日の日付（YYYY/MM/DD）",
  "weather": "天候",
  "temperature": "気温",
  "work_hours": "作業時間",
  "overtime": "残業時間",
  "workers": [
    {
      "company": "会社名",
      "job_type": "職種",
      "foreman": "職長人数",
      "skilled": "技能者人数",
      "apprentice": "見習い人数",
      "total": "合計人工",
      "work_category": "工種",
      "description": "作業内容"
    }
  ],
  "safety": {
    "ky_done": "KY実施（true/false）",
    "near_miss": "ヒヤリハット有無（true/false）",
    "near_miss_detail": "ヒヤリハット内容"
  },
  "materials": [
    {
      "name": "資材名",
      "quantity": "数量"
    }
  ],
  "notes": "特記事項",
  "confirm_items": ["確認が必要な項目のリスト"]
}

ルール：
1. 人数が「5人」とだけ言われた場合、職長1＋技能者の残りと推定
2. 会社名が不明な場合はnullにしてconfirm_itemsに追加
3. 日付が不明な場合は2026/09/15を使用してください。必ずYYYY/MM/DD形式で出力
4. JSON以外の文字は出力しないでください"""

    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcribed_text}
        ],
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        print("GPT error: " + str(response.status_code) + " - " + response.text)
        return None

    try:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            split_lines = content.split(NEWLINE)
            split_lines = split_lines[1:]
            if split_lines and split_lines[-1].strip() == "```":
                split_lines = split_lines[:-1]
            content = NEWLINE.join(split_lines)
        nippo_data = json.loads(content)
        return nippo_data
    except Exception as e:
        print("JSON parse error: " + str(e))
        return None


def format_nippo_message(nippo_data):
    if nippo_data is None:
        return "日報の変換に失敗しました。もう一度音声を送ってください。"

    lines = []
    lines.append("--- 日報を作成しました！ ---")
    lines.append("")

    date_val = nippo_data.get("date", "不明")
    weather = nippo_data.get("weather", "不明")
    temp = nippo_data.get("temperature", "")
    lines.append("日付：" + str(date_val))
    weather_line = "天候：" + str(weather)
    if temp:
        weather_line = weather_line + " " + str(temp)
    lines.append(weather_line)

    work_hours = nippo_data.get("work_hours", "")
    overtime = nippo_data.get("overtime", "")
    if work_hours:
        lines.append("作業時間：" + str(work_hours))
    if overtime:
        lines.append("残業：" + str(overtime))

    workers = nippo_data.get("workers", [])
    if workers:
        lines.append("")
        lines.append("【作業員配置】")
        total_workers = 0
        for w in workers:
            company = w.get("company", "不明")
            job_type = w.get("job_type", "")
            foreman = int(str(w.get("foreman", 0) or 0))
            skilled = int(str(w.get("skilled", 0) or 0))
            apprentice = int(str(w.get("apprentice", 0) or 0))
            total = int(str(w.get("total", 0) or 0))
            work_cat = w.get("work_category", "")
            desc = w.get("description", "")
            company_line = str(company)
            if job_type:
                company_line = company_line + "（" + str(job_type) + "）"
            lines.append(company_line)
            lines.append("  職長" + str(foreman) + " 技能者" + str(skilled) + " 見習" + str(apprentice) + " = " + str(total) + "人工")
            if work_cat or desc:
                detail = "  -> " + str(work_cat)
                if desc:
                    detail = detail + "：" + str(desc)
                lines.append(detail)
            total_workers = total_workers + int(str(total))
        lines.append("")
        lines.append("合計：" + str(total_workers) + "人工")

    safety = nippo_data.get("safety", {})
    if safety:
        lines.append("")
        lines.append("【安全管理】")
        ky = safety.get("ky_done", None)
        hh = safety.get("near_miss", None)
        if ky is True:
            lines.append("KY：実施済")
        elif ky is False:
            lines.append("KY：未実施")
        if hh is True:
            detail = safety.get("near_miss_detail", "")
            hh_line = "ヒヤリハット：あり"
            if detail:
                hh_line = hh_line + "（" + str(detail) + "）"
            lines.append(hh_line)
        elif hh is False:
            lines.append("ヒヤリハット：なし")

    materials = nippo_data.get("materials", [])
    if materials:
        lines.append("")
        lines.append("【搬入資材】")
        for m in materials:
            name = m.get("name", "")
            qty = m.get("quantity", "")
            if name:
                mat_line = "・" + str(name)
                if qty:
                    mat_line = mat_line + "（" + str(qty) + "）"
                lines.append(mat_line)

    notes = nippo_data.get("notes", None)
    if notes:
        lines.append("")
        lines.append("【特記事項】")
        lines.append(str(notes))

    confirm = nippo_data.get("confirm_items", [])
    if confirm:
        lines.append("")
        lines.append("【確認が必要な項目】")
        for c in confirm:
            lines.append("・" + str(c))

    lines.append("")
    lines.append("この内容でOKですか？")
    lines.append("修正があれば音声またはテキストで送ってください。")

    return NEWLINE.join(lines)