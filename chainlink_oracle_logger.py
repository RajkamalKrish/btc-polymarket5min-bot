# btc_5m_candle_logger.py

import websocket
import json
from datetime import datetime

WS_URL = "wss://ws-live-data.polymarket.com"

TARGET_SYMBOL = "btc/usd"

# ============================================================
# CANDLE STORAGE
# ============================================================

current_candle = None
current_bucket = None

# ============================================================
# HELPERS
# ============================================================

def get_5m_bucket(dt):
    minute = (dt.minute // 5) * 5
    return dt.replace(minute=minute, second=0, microsecond=0)

# ============================================================
# OPEN
# ============================================================

def on_open(ws):

    print("CONNECTED")

    subscribe_msg = {
        "action": "subscribe",
        "subscriptions": [
            {
                "topic": "crypto_prices_chainlink",
                "type": "*",
                "filters": ""
            }
        ]
    }

    ws.send(json.dumps(subscribe_msg))

# ============================================================
# MESSAGE
# ============================================================

def on_message(ws, message):

    global current_candle
    global current_bucket

    try:

        data = json.loads(message)

        if data.get("topic") != "crypto_prices_chainlink":
            return

        payload = data.get("payload", {})

        symbol = payload.get("symbol", "").lower()

        if symbol != TARGET_SYMBOL:
            return

        price = float(payload.get("value"))

        timestamp = payload.get("timestamp")

        dt = datetime.utcfromtimestamp(timestamp / 1000)

        bucket = get_5m_bucket(dt)

        # ====================================================
        # NEW CANDLE
        # ====================================================

        if current_bucket != bucket:

            # print previous candle
            if current_candle:

                direction = "UP"

                if current_candle["close"] < current_candle["open"]:
                    direction = "DOWN"

                print("\n================================================")
                print("5 MIN CANDLE CLOSED")
                print("================================================")
                print("TIME  :", current_bucket)
                print("OPEN  :", round(current_candle["open"], 2))
                print("HIGH  :", round(current_candle["high"], 2))
                print("LOW   :", round(current_candle["low"], 2))
                print("CLOSE :", round(current_candle["close"], 2))
                print("MOVE  :", direction)

            # start new candle
            current_bucket = bucket

            current_candle = {
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }

        # ====================================================
        # UPDATE CANDLE
        # ====================================================

        current_candle["high"] = max(
            current_candle["high"],
            price
        )

        current_candle["low"] = min(
            current_candle["low"],
            price
        )

        current_candle["close"] = price

    except Exception as e:
        print("ERROR:", e)

# ============================================================
# ERROR
# ============================================================

def on_error(ws, error):
    print("ERROR:", error)

# ============================================================
# CLOSE
# ============================================================

def on_close(ws, close_status_code, close_msg):
    print("CLOSED")

# ============================================================
# MAIN
# ============================================================

ws = websocket.WebSocketApp(
    WS_URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
