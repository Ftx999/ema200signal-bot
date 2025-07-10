from flask import Flask
import pandas as pd
import ccxt
from ta.trend import EMAIndicator
from datetime import datetime
import pytz
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '🟢 EMA200 Signal Bot 正常運作中'

@app.route('/run')
def run_signal():
    try:
        tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(tz).strftime('%Y-%m-%d %H:%M')

        # 初始化 MEXC 交易所
        exchange = ccxt.mexc()
        exchange.load_markets()

        # 你可以自行增加更多幣對
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'OP/USDT', 'DOGE/USDT']

        results = []
        for symbol in symbols:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=210)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

                # 計算 EMA200
                df['ema200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()

                # 取得上一根 K 線的收盤價與 EMA200
                prev_close = df['close'].iloc[-2]
                prev_ema = df['ema200'].iloc[-2]

                if prev_close > prev_ema:
                    msg = f"✅ {symbol} 在 {now} 上一根15分鐘K線收盤突破 EMA200"
                else:
                    msg = f"❌ {symbol} 在 {now} 尚未突破 EMA200"

                print(msg)
                results.append(msg)

            except Exception as e:
                err_msg = f"❌ {symbol} 錯誤: {e}"
                print(err_msg)
                results.append(err_msg)

        return '<br>'.join(results)

    except Exception as e:
        print(f"🚨 全域錯誤: {e}")
        return f"🚨 發生錯誤: {e}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

