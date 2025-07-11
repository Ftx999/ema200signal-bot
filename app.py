import ccxt
import pandas as pd
import ta
import pytz
import requests
import time
import threading
from datetime import datetime
from flask import Flask

# Telegram 設定
TELEGRAM_TOKEN = '7503875589:AAHDFUd4XwUv3bgj7Lc6H1lD1VZeGNN4UB8'
CHAT_ID = '232584348'

tz = pytz.timezone('Asia/Taipei')
exchange = ccxt.mexc({'options': {'defaultType': 'swap'}})
app = Flask(__name__)

# 發送 Telegram 訊息
def send_telegram_message(text):
    print(f"📬 準備發送 Telegram 訊息：\n{text}")
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': text}
    try:
        response = requests.post(url, data=payload)
        print(f"📨 Telegram 回應：{response.text}")
    except Exception as e:
        print(f"❌ Telegram 發送失敗: {e}")

# 偵測 crossing up 的交易對
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
            kline_time = df.index[-2].strftime('%Y-%m-%d %H:%M')
            return f"✅ {symbol} 在 {kline_time} crossing up EMA200"
        return None

    except Exception as e:
        print(f"❌ {symbol} 錯誤: {e}")
        return None

# 掃描所有交易對
def scan_symbols():
    print("🔍 掃描中...")
    results = []
    try:
        markets = exchange.load_markets()
        usdt_pairs = [s for s in markets if 'USDT' in s and markets[s]['type'] == 'swap']
    except Exception as e:
        print(f"❌ 無法載入市場資料: {e}")
        return results

    for i, symbol in enumerate(usdt_pairs):
        print(f"[{i+1}/{len(usdt_pairs)}] 檢查 {symbol}")
        result = fetch_signal(symbol)
        if result:
            results.append(result)

    return results

# 每 15 分鐘執行的工作
def job():
    print(f"⏰ {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')} 開始掃描")
    results = scan_symbols()

    if results:
        summary = "\n".join(results)
    else:
        summary = "🟢 本輪無任何 crossing up 結果"

    send_telegram_message(summary)
    print("✅ 掃描與通知完成")

# Flask 路由
@app.route('/')
def home():
    return "✅ EMA200 Signal Bot 正常運行中"

@app.route('/run')
def run():
    job()
    return "✅ 手動觸發掃描完成"

# 背景排程
def start_scheduler():
    schedule.every(15).minutes.at(":00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

# 啟動主程式
if __name__ == '__main__':
    print("🚀 EMA200 Crossing Up Bot 啟動！")
    job()
    threading.Thread(target=start_scheduler, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
