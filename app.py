from flask import Flask
import ccxt
import pandas as pd
import ta
import pytz
import requests
from datetime import datetime

# === Telegram 設定 ===
TELEGRAM_TOKEN = '7503875589:AAHDFUd4XwUv3bgj7Lc6H1lD1VZeGNN4UB8'
CHAT_ID = '232584348'

# === 系統初始化 ===
tz = pytz.timezone('Asia/Taipei')
exchange = ccxt.mexc({'options': {'defaultType': 'swap'}})
app = Flask(__name__)

# === 發送 Telegram 訊息 ===
def send_telegram_message(text):
    print(f"📬 準備發送 Telegram 訊息：{text}")
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': text}
    try:
        response = requests.post(url, data=payload)
        print(f"📨 Telegram 回應：{response.text}")
    except Exception as e:
        print(f"❌ Telegram 發送失敗: {e}")

# === 檢查 crossing up 條件 ===
def fetch_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=210)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert(tz)
        df.set_index('timestamp', inplace=True)
        if len(df) < 3:
            return None

        ema = ta.trend.EMAIndicator(close=df['close'], window=200)
        df['ema200'] = ema.ema_indicator()

        if df['close'].iloc[-3] < df['ema200'].iloc[-3] and df['close'].iloc[-2] > df['ema200'].iloc[-2]:
            now = datetime.now(tz).strftime('%Y-%m-%d %H:%M')
            return f"✅ {symbol} 在 {now} crossing up EMA200"
        return None
    except Exception as e:
        print(f"❌ {symbol} 錯誤: {e}")
        return None

# === 掃描所有幣對並一次回報 ===
def scan_symbols():
    print("🔍 開始掃描 MEXC USDT 永續合約...")
    try:
        markets = exchange.load_markets()
        usdt_pairs = [s for s in markets if 'USDT' in s and markets[s]['type'] == 'swap']
    except Exception as e:
        print(f"❌ 無法載入市場資料: {e}")
        return "市場資料載入錯誤"

    messages = []
    for i, symbol in enumerate(usdt_pairs):
        print(f"[{i+1}/{len(usdt_pairs)}] 檢查 {symbol}")
        result = fetch_signal(symbol)
        if result:
            messages.append(result)

    if messages:
        combined_message = "📊 本次符合條件的交易對：\n" + "\n".join(messages)
        send_telegram_message(combined_message)
        return combined_message
    else:
        print("✅ 無符合條件的交易對")
        return "✅ 無符合 crossing up EMA200 條件的交易對"

# === 路由 ===
@app.route('/')
def home():
    return "✅ EMA200 Signal Bot 運行中"

@app.route('/run')
def run():
    result = scan_symbols()
    return result

# === 啟動 Flask ===
if __name__ == '__main__':
    print("🚀 EMA200 Crossing Up Bot 啟動中！")
    app.run(host='0.0.0.0', port=10000)
