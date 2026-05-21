# btc_5m_logger.py

import websocket
import json
from datetime import datetime

WS_URL = "wss://ws-live-data.polymarket.com"

# ============================================================
# SETTINGS
# ============================================================

TARGET_SYMBOL = "btc/usd"

# ============================================================
# OPEN
# ============================================================

def on_open(ws):

    print("================================================")
    print("CONNECTED TO POLYMARKET RTDS")
    print("================================================")

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

    print("\nSubscribed to BTC Chainlink feed")

# ============================================================
# MESSAGE
# ============================================================

def on_message(ws, message):

    try:

        data = json.loads(message)

        if data.get("topic") != "crypto_prices_chainlink":
            return

        payload = data.get("payload", {})

        symbol = payload.get("symbol", "").lower()

        # ====================================================
        # ONLY BTC
        # ====================================================

        if symbol != TARGET_SYMBOL:
            return

        price = payload.get("value")
        timestamp = payload.get("timestamp")

        readable_time = datetime.utcfromtimestamp(
            timestamp / 1000
        ).strftime("%Y-%m-%d %H:%M:%S")

        print("\n================================================")
        print("BTC LIVE PRICE")
        print("================================================")
        print("TIME   :", readable_time)
        print("SYMBOL :", symbol)
        print("PRICE  :", price)

    except Exception as e:
        print("ERROR:", e)

# ============================================================
# ERROR
# ============================================================

def on_error(ws, error):
    print("\nERROR:")
    print(error)

# ============================================================
# CLOSE
# ============================================================

def on_close(ws, close_status_code, close_msg):
    print("\nCLOSED")
    print(close_status_code)
    print(close_msg)

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
