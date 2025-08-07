from flask import Flask, request
import requests
import pandas as pd
import numpy as np
import websocket
import json

# بارگذاری تنظیمات از config.json
with open("config.json", "r") as f:
    config = json.load(f)

BOT_TOKEN = config["BOT_TOKEN"]
CHAT_ID = config["CHAT_ID"]

app = Flask(__name__)

@app.route("/")
def home():
    return "🚀 Crypto Signal Bot is running..."

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

# تابع برای اتصال به Binance WebSocket
def on_message(ws, message):
    data = json.loads(message)
    symbol = data['s']
    price = float(data['c'])

    # الگوریتم نمونه برای تشخیص پامپ
    if 'last_price' not in on_message.__dict__:
        on_message.last_price = {}
    if symbol not in on_message.last_price:
        on_message.last_price[symbol] = price

    change = ((price - on_message.last_price[symbol]) / on_message.last_price[symbol]) * 100

    if change >= 2:  # پامپ بیش از ۲٪
        signal_msg = f"""
🚀 پامپ شناسایی شد!
📌 {symbol}
💰 قیمت فعلی: {price}
🎯 تغییر: {change:.2f}%
📈 پیشنهاد: بررسی ورود Long
        """
        send_to_telegram(signal_msg)

    on_message.last_price[symbol] = price

def on_error(ws, error):
    print("❌ WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("🔴 WebSocket closed")

def on_open(ws):
    print("🟢 WebSocket connection opened")
    payload = {
        "method": "SUBSCRIBE",
        "params": [
            f"{symbol.lower()}@ticker"
            for symbol in SYMBOLS
        ],
        "id": 1
    }
    ws.send(json.dumps(payload))

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]  # کوین‌های اصلی

if __name__ == "__main__":
    # اجرای Flask API در یک ترد جدا
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()

    # اجرای WebSocket برای دریافت قیمت‌ها
    socket = "wss://stream.binance.com:9443/ws"
    ws = websocket.WebSocketApp(socket, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.run_forever()
