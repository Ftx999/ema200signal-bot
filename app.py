from flask import Flask
import ccxt
import pandas as pd
import ta
import pytz
from datetime import datetime

app = Flask(__name__)
tz = pytz.timezone('Asia/Taipei')
exchange = ccxt.mexc({'options': {'defaultType': 'swap'}})

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
            return True
    except:
        return None
    return False

def scan_symbols():
    markets = exchange.load_markets()
    usdt_pairs = [s for s in markets if 'USDT' in s and markets[s]['type'] == 'swap']
    result = []
    for symbol in usdt_pairs:
        if fetch_signal(symbol):
            result.append(symbol)
    return result

@app.route('/')
def home():
    return "🟢 EMA200 Signal Bot 正常運作中"

@app.route('/run', methods=['GET'])
def run():
    result = scan_symbols()
    if result:
        return f"✅ Crossing up EMA200: {result}"
    else:
        return "⏳ 沒有符合 crossing up EMA200 的交易對"

if __name__ == '__main__':
    app.run()
