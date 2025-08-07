from flask import Flask, request
import requests
import pandas as pd
import numpy as np
import time

app = Flask(__name__)

BOT_TOKEN = "8416346676:AAEE7IXZ3QN7qs5e9DkAwskxtsC2QbTgILY"
CHAT_ID = "46773935"

BINANCE_URL = "https://api.binance.com/api/v3/klines"

WATCH_LIST = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]

# ارسال پیام به تلگرام
def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload)

# دریافت داده از Binance
def get_klines(symbol, interval, limit=100):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    data = requests.get(BINANCE_URL, params=params).json()
    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume","close_time",
        "quote_asset_volume","num_trades","taker_buy_base","taker_buy_quote","ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df

# محاسبه RSI
def rsi(df, period=14):
    delta = df["close"].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(period).mean()
    avg_loss = pd.Series(loss).rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# محاسبه EMA
def ema(df, period):
    return df["close"].ewm(span=period, adjust=False).mean()

# بررسی شرایط سیگنال ۹۵٪
def check_signal(symbol):
    df = get_klines(symbol, "5m", 100)
    df["RSI"] = rsi(df)
    df["EMA50"] = ema(df, 50)
    df["EMA200"] = ema(df, 200)

    last = df.iloc[-1]
    rsi_val = last["RSI"]
    ema50 = last["EMA50"]
    ema200 = last["EMA200"]
    close = last["close"]

    # شرایط لانگ
    if rsi_val > 50 and ema50 > ema200 and close > ema50:
        tp1 = round(close * 1.005, 4)
        tp2 = round(close * 1.01, 4)
        tp3 = round(close * 1.015, 4)
        sl = round(close * 0.99, 4)
        send_to_telegram(f"🚀 سیگنال ۹۵٪ لانگ {symbol}\nEntry: {close}\nTP1: {tp1}\nTP2: {tp2}\nTP3: {tp3}\nSL: {sl}\nLeverage: 5x")

    # شرایط شورت
    elif rsi_val < 50 and ema50 < ema200 and close < ema50:
        tp1 = round(close * 0.995, 4)
        tp2 = round(close * 0.99, 4)
        tp3 = round(close * 0.985, 4)
        sl = round(close * 1.01, 4)
        send_to_telegram(f"📉 سیگنال ۹۵٪ شورت {symbol}\nEntry: {close}\nTP1: {tp1}\nTP2: {tp2}\nTP3: {tp3}\nSL: {sl}\nLeverage: 5x")

@app.route("/")
def home():
    return "🚀 Bot is alive and watching the charts!"

@app.route("/send", methods=["POST"])
def send_signal():
    data = request.json
    message = data.get("message", "📡 سیگنال جدید دریافت شد.")
    send_to_telegram(message)
    return {"status": "sent"}, 200

# شروع مانیتورینگ
send_to_telegram("✅ ربات فعال شد و ماژول سیگنال‌دهی ۹۵٪ روشن است.")

if __name__ == "__main__":
    while True:
        for coin in WATCH_LIST:
            try:
                check_signal(coin)
            except Exception as e:
                print(f"Error checking {coin}: {e}")
        time.sleep(60)  # هر 1 دقیقه بررسی مجدد
