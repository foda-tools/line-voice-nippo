import json
import hashlib
import hmac
import base64
from flask import Flask, request, abort
from config import LINE_CHANNEL_SECRET, APP_PORT, DEBUG_MODE
from handlers.line_handler import handle_message, send_reply

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return json.dumps({"status": "ok", "app": "LINE voice nippo", "version": "1.0"}), 200, {"Content-Type": "application/json"}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    if not verify_signature(body, signature):
        abort(403)
    try:
        events = json.loads(body).get("events", [])
        for event in events:
            event_type = event.get("type", "")
            if event_type == "message":
                handle_message(event)
            elif event_type == "follow":
                welcome = """お仕事お疲れ様です！

LINE音声日報ツールへようこそ！

音声メッセージで日報を送るだけで
自動で日報が完成します。

「ヘルプ」と送ると使い方が見れます。"""
                send_reply(event["replyToken"], welcome)
    except Exception as e:
        print("error: " + str(e))
    return "OK", 200

def verify_signature(body, signature):
    if not LINE_CHANNEL_SECRET:
        return False
    hash_value = hmac.new(LINE_CHANNEL_SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    expected = base64.b64encode(hash_value).decode("utf-8")
    return hmac.compare_digest(signature, expected)

if __name__ == "__main__":
    print("=" * 50)
    print("LINE voice nippo v1.0 starting...")
    print("Port: " + str(APP_PORT))
    print("=" * 50)
    app.run(host="0.0.0.0", port=APP_PORT, debug=DEBUG_MODE)