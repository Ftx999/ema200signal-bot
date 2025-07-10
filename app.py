from flask import Flask
import ccxt
import pandas as pd
import ta
from datetime import datetime, timedelta
import pytz
import os

app = Flask(__name__)

# 設定 MEXC 交易所
exchange = ccxt.mexc({
    'enableRateLimit': True
})

# 設定時區（台灣）
tz = pytz.timezone('Asia/Taipei')


@app.route('/')
def home():
    return "🟢 EMA200 Signal Bot 正常運作中"


@app.route('/run')
def run_signal():
    try:
        symbols = exchange.load_markets()
        spot_pairs = [s for s in symbols if s.endswith('/USDT') and symbols[s]['spot']]
    except Exception as e:
        return f"❌ 無法讀取交易對：{e}"

    output = []
    now = datetime.now(tz).strftime('%Y-%m-%d %H:%M')

    for symbol in spot_pairs:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=210)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            if df.shape[0] < 201:
                continue  # 資料不夠就跳過

            df['ema200'] = ta.trend.ema_indicator(df['close'], window=200)

            # 檢查上一根 K 線 crossing up
            prev_close = df.iloc[-3]['close']
            last_close = df.iloc[-2]['close']
            prev_ema = df.iloc[-3]['ema200']
            last_ema = df.iloc[-2]['ema200']

            if prev_close < prev_ema and last_close > last_ema:
                output.append(f"✅ {symbol} 在 {now} 出現上穿 EMA200（crossing up）")

        except Exception as e:
            # 可加 log: print(f"❌ {symbol} 出錯: {e}")
            continue

    if not output:
        return f"🔍 {now} 無交易對出現 crossing up EMA200"
    else:
        return "<br>".join(output)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
