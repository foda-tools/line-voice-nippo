import requests
from config import OPENAI_API_KEY, LINE_CHANNEL_ACCESS_TOKEN

def get_audio_from_line(message_id):
    url = "https://api-data.line.me/v2/bot/message/" + message_id + "/content"
    headers = {"Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print("Audio download error: " + str(response.status_code))
        return None

def transcribe_audio(audio_data):
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": "Bearer " + OPENAI_API_KEY}
    files = {"file": ("audio.m4a", audio_data, "audio/m4a")}
    data = {"model": "whisper-1", "language": "ja"}
    response = requests.post(url, headers=headers, files=files, data=data)
    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        print("Whisper error: " + str(response.status_code) + " - " + response.text)
        return None

def process_voice_message(message_id):
    audio_data = get_audio_from_line(message_id)
    if audio_data is None:
        return "音声データの取得に失敗しました。もう一度送ってください。"
    text = transcribe_audio(audio_data)
    if text is None:
        return "音声の変換に失敗しました。もう一度送ってください。"
    return text