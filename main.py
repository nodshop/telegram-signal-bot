from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "8416346676:AAEE7IXZ3QN7qs5e9DkAwskxtsC2QbTgILY"
CHAT_ID = "46773935"

@app.route("/")
def home():
    return "🚀 Bot is alive and watching the charts!"

@app.route("/send", methods=["POST"])
def send_signal():
    data = request.json
    message = data.get("message", "📡 سیگنال جدید دریافت شد.")
    send_to_telegram(message)
    return {"status": "sent"}, 200

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)