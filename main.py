from flask import Flask, request
import requests
import pandas as pd
import time
import threading
import ta

# ----- تنظیمات -----
BOT_TOKEN = "8416346676:AAEE7IXZ3QN7qs5e9DkAwskxtsC2QbTgILY"
CHAT_ID = "46773935"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", 
           "ADAUSDT", "MATICUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT"]

TF_MAP = {"5m": "5m", "15m": "15m", "1h": "1h"}
API_URL = "https://api.binance.com/api/v3/klines"

# ----- اتصال تلگرام -----
def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload)

# ----- گرفتن داده کندل -----
def get_klines(symbol, interval, limit=100):
    url = f"{API_URL}?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        'timestamp','open','high','low','close','volume','c','d','e','f','g','ignore'
    ])
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df

# ----- الگوریتم سیگنال -----
def analyze_signal(symbol):
    directions = {}
    for tf in TF_MAP:
        df = get_klines(symbol, TF_MAP[tf])
        rsi = ta.momentum.RSIIndicator(df["close"], 14).rsi().iloc[-1]
        macd = ta.trend.MACD(df["close"]).macd_diff().iloc[-1]
        ema50 = ta.trend.EMAIndicator(df["close"], 50).ema_indicator().iloc[-1]
        ema200 = ta.trend.EMAIndicator(df["close"], 200).ema_indicator().iloc[-1]

        if rsi > 55 and macd > 0 and ema50 > ema200:
            directions[tf] = "LONG"
        elif rsi < 45 and macd < 0 and ema50 < ema200:
            directions[tf] = "SHORT"
        else:
            directions[tf] = "NONE"

    # بررسی یکسان بودن تایم‌فریم‌ها
    if all(v == "LONG" for v in directions.values()):
        strength = "✅ قوی"
        leverage = "10x-15x"
        return f"🚀 سیگنال LONG {symbol}\nقدرت: {strength}\nاهرم: {leverage}\nTP1: +0.5%\nTP2: +1%\nTP3: +1.5%\nSL: -0.5%"
    elif all(v == "SHORT" for v in directions.values()):
        strength = "✅ قوی"
        leverage = "10x-15x"
        return f"📉 سیگنال SHORT {symbol}\nقدرت: {strength}\nاهرم: {leverage}\nTP1: -0.5%\nTP2: -1%\nTP3: -1.5%\nSL: +0.5%"
    return None

# ----- اسکن مداوم بازار -----
def scanner():
    while True:
        for symbol in SYMBOLS:
            try:
                signal = analyze_signal(symbol)
                if signal:
                    send_to_telegram(signal)
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
        time.sleep(60)  # هر ۱ دقیقه یکبار

# ----- وب‌سرور -----
app = Flask(__name__)

@app.route("/")
def home():
    return "🚀 Pump Signal Bot 95% is running!"

@app.route("/send", methods=["POST"])
def send_signal():
    data = request.json
    message = data.get("message", "📡 سیگنال جدید دریافت شد.")
    send_to_telegram(message)
    return {"status": "sent"}, 200

# اجرای اسکنر در بک‌گراند
threading.Thread(target=scanner, daemon=True).start()

if __name__ == "__main__":
    send_to_telegram("✅ ربات سیگنال‌دهی ۹۵٪ فعال شد.")
    app.run(host="0.0.0.0", port=5000)
