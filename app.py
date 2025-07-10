from flask import Flask
import ccxt
import pandas as pd
import ta
import pytz
from datetime import datetime

tz = pytz.timezone('Asia/Taipei')
app = Flask(__name__)

# 初始化 MEXC 永續合約交易所
exchange = ccxt.mexc({
    'options': {
        'defaultType': 'swap'
    }
})

def fetch_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=210)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert(tz)
        df.set_index('timestamp', inplace=True)

        if len(df) < 3:
            print(f"⏭️ {symbol} 資料不足")
            return None

        ema = ta.trend.EMAIndicator(close=df['close'], window=200)
        df['ema200'] = ema.ema_indicator()

        # crossing up：前一根在下，上一根在上
        if df['close'].iloc[-3] < df['ema200'].iloc[-3] and df['close'].iloc[-2] > df['ema200'].iloc[-2]:
            now = datetime.now(tz).strftime('%Y-%m-%d %H:%M')
            message = f"✅ {symbol} 在 {now} 上一根15分鐘K線 crossing up EMA200"
            print(message)
            return message
        return None

    except Exception as e:
        print(f"❌ {symbol} 錯誤: {e}")
        return None

def scan_symbols():
    print("🔍 掃描中...")
    try:
        markets = exchange.load_markets()
        usdt_pairs = [s for s in markets if 'USDT' in s and markets[s]['type'] == 'swap']
    except Exception as e:
        return f"❌ 無法載入市場資料: {e}"

    messages = []
    for symbol in usdt_pairs:
        result = fetch_signal(symbol)
        if result:
            messages.append(result)
    if not messages:
        return "✅ 沒有符合 crossing up 條件的交易對"
    return "\n".join(messages)

# 網頁模式：用 /run 觸發
@app.route('/run')
def run():
    result = scan_symbols()
    return result

# 如果是本機執行（例如 python app.py）
if __name__ == '__main__':
    print("🚀 EMA200 Crossing Up Bot 啟動！")
    scan_symbols()
    app.run(host='0.0.0.0', port=10000)

