from flask import Flask
import ccxt
import pandas as pd
import ta
import pytz
from datetime import datetime

# 設定時區
tz = pytz.timezone('Asia/Taipei')

# 初始化 Flask 應用
app = Flask(__name__)

# 初始化 MEXC 永續合約交易所
exchange = ccxt.mexc({
    'options': {
        'defaultType': 'swap'  # 使用 swap 表示永續合約
    }
})

def fetch_signal(symbol):
    try:
        # 抓取15分鐘K線資料
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=210)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert(tz)
        df.set_index('timestamp', inplace=True)

        if len(df) < 3:
            print(f"⏭️ {symbol} 資料不足")
            return None

        # 計算EMA200
        ema = ta.trend.EMAIndicator(close=df['close'], window=200)
        df['ema200'] = ema.ema_indicator()

        # crossing up 條件：倒數第3根收盤在 EMA200 下，倒數第2根收盤在 EMA200 上
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
    print("🔍 開始掃描所有 MEXC USDT 合約交易對...")
    try:
        markets = exchange.load_markets()
        usdt_pairs = [s for s in markets if 'USDT' in s and markets[s].get('type') == 'swap']
    except Exception as e:
        return f"❌ 無法載入市場資料: {e}"

    messages = []
    for idx, symbol in enumerate(usdt_pairs):
        print(f"➡️ ({idx + 1}/{len(usdt_pairs)}) 掃描 {symbol} 中...")
        result = fetch_signal(symbol)
        if result:
            messages.append(result)

    if not messages:
        return "✅ 沒有符合 crossing up EMA200 條件的交易對"
    return "\n".join(messages)

# 網頁模式：用 /run 觸發掃描
@app.route('/run')
def run():
    return scan_symbols()

@app.route('/')
def home():
    return "✅ EMA200 Signal Bot 正常運行中，請訪問 /run 觸發掃描。"


# 本地執行時自動掃一次並啟動 server
if __name__ == '__main__':
    print("🚀 EMA200 Crossing Up Bot 已啟動！")
    scan_symbols()
    app.run(host='0.0.0.0', port=10000)
