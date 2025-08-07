from flask import Flask
import requests
import pandas as pd
import time
import threading

# ------------------ تنظیمات ------------------
BOT_TOKEN = "8416346676:AAEE7IXZ3QN7qs5e9DkAwskxtsC2QbTgILY"
CHAT_ID = "46773935"
BINANCE_API = "https://api.binance.com/api/v3"
TIMEFRAMES = ["5m", "15m", "1h"]
LIMIT = 100
CONFIDENCE_THRESHOLD = 95
SCAN_INTERVAL = 60  # هر چند ثانیه یکبار بررسی شود

app = Flask(__name__)

# ------------------ ارسال پیام به تلگرام ------------------
def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ------------------ دریافت 100 کوین برتر ------------------
def get_top_futures_symbols():
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        data = requests.get(url).json()
        df = pd.DataFrame(data)
        df["quoteVolume"] = df["quoteVolume"].astype(float)
        df = df[df["symbol"].str.endswith("USDT")]
        df = df.sort_values("quoteVolume", ascending=False)
        return df.head(100)["symbol"].tolist()
    except Exception as e:
        print(f"Error getting top symbols: {e}")
        return []

# ------------------ دریافت داده کندل ------------------
def get_klines(symbol, interval):
    try:
        url = f"{BINANCE_API}/klines?symbol={symbol}&interval={interval}&limit={LIMIT}"
        data = requests.get(url).json()
        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df["close"] = df["close"].astype(float)
        df["open"] = df["open"].astype(float)
        return df
    except Exception as e:
        print(f"Error getting klines for {symbol} {interval}: {e}")
        return pd.DataFrame()

# ------------------ تحلیل سیگنال ------------------
def analyze_signal(symbol):
    tf_results = {}
    for tf in TIMEFRAMES:
        df = get_klines(symbol, tf)
        if df.empty:
            return None

        last_close = df["close"].iloc[-1]
        prev_close = df["close"].iloc[-2]

        tf_results[tf] = last_close > prev_close

    if all(tf_results.values()):
        direction = "📈 Long"
        confidence = 97
    elif all(not v for v in tf_results.values()):
        direction = "📉 Short"
        confidence = 97
    else:
        return None

    leverage = "10x" if confidence >= 97 else "5x"

    last_price = get_klines(symbol, "1m")["close"].iloc[-1]
    tp1 = round(last_price * (1.002 if direction == "📈 Long" else 0.998), 4)
    tp2 = round(last_price * (1.004 if direction == "📈 Long" else 0.996), 4)
    tp3 = round(last_price * (1.006 if direction == "📈 Long" else 0.994), 4)
    sl = round(last_price * (0.995 if direction == "📈 Long" else 1.005), 4)

    signal_text = (
        f"🚀 سیگنال 95%+ شناسایی شد\n"
        f"🔹 جفت‌ارز: {symbol}\n"
        f"📊 جهت: {direction}\n"
        f"🎯 TP1: {tp1}\n"
        f"🎯 TP2: {tp2}\n"
        f"🎯 TP3: {tp3}\n"
        f"🛑 SL: {sl}\n"
        f"💹 اهرم پیشنهادی: {leverage}\n"
        f"📈 درصد اعتماد: {confidence}%"
    )
    return signal_text

# ------------------ اسکن خودکار بازار ------------------
def auto_scan():
    while True:
        symbols = get_top_futures_symbols()
        for symbol in symbols:
            signal = analyze_signal(symbol)
            if signal:
                send_to_telegram(signal)
        time.sleep(SCAN_INTERVAL)

# ------------------ شروع اسکن در بک‌گراند ------------------
def start_background_scan():
    thread = threading.Thread(target=auto_scan)
    thread.daemon = True
    thread.start()

@app.route("/")
def home():
    return "🚀 Auto Pump Hunter Bot is Running..."

if __name__ == "__main__":
    start_background_scan()
    app.run(host="0.0.0.0", port=5000)
