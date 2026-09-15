import requests
from config import LINE_CHANNEL_ACCESS_TOKEN
from services.whisper_service import process_voice_message
from services.gpt_service import convert_to_nippo, format_nippo_message
from services.data_service import save_nippo, get_monthly_summary

def handle_message(event):
    message_type = event["message"]["type"]
    reply_token = event["replyToken"]
    user_id = event["source"]["userId"]
    if message_type == "audio":
        message_id = event["message"]["id"]
        transcribed_text = process_voice_message(message_id)
        if transcribed_text.startswith("音声"):
            send_reply(reply_token, transcribed_text)
            return
        nippo_data = convert_to_nippo(transcribed_text)
        if nippo_data is not None:
            save_nippo(user_id, nippo_data)
        reply_text = format_nippo_message(nippo_data)
        send_reply(reply_token, reply_text)
    elif message_type == "text":
        text = event["message"]["text"]
        reply_text = handle_text_command(text, user_id)
        send_reply(reply_token, reply_text)
    else:
        send_reply(reply_token, "音声メッセージまたはテキストで日報を送ってください。")

def handle_text_command(text, user_id):
    text = text.strip()
    if text == "ヘルプ":
        return """【使い方】

音声メッセージ → 日報を自動作成
テキスト → 日報を入力

【コマンド一覧】
・「ヘルプ」→ この画面
・「今月の集計」→ 月次サマリー
・「ステータス」→ 接続状態確認"""
    elif text == "ステータス":
        return """LINE音声日報ツール v1.0

BOT接続：正常
サーバー：稼働中

ユーザーID：""" + user_id[:8] + "..."
    elif text == "今月の集計":
        return get_monthly_summary(user_id)
    else:
        return """以下のコマンドが使えます：

音声メッセージ → 日報作成
「ヘルプ」→ 使い方
「ステータス」→ 接続確認
「今月の集計」→ 月次サマリー"""

def send_reply(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN}
    body = {"replyToken": reply_token, "messages": [{"type": "text", "text": text}]}
    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        print("Reply error: " + str(response.status_code) + " - " + response.text)
    return response