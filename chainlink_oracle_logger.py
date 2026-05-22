# btc_5m_candle_logger.py

import websocket
import json
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

WS_URL = "wss://ws-live-data.polymarket.com"

TARGET_SYMBOL = "btc/usd"

# ============================================================
# GLOBALS
# ============================================================

current_candle = None
current_bucket = None

# ============================================================
# HELPERS
# ============================================================

def get_5m_bucket(dt):
    """
    Convert timestamp into 5-minute candle bucket
    """

    minute = (dt.minute // 5) * 5

    return dt.replace(
        minute=minute,
        second=0,
        microsecond=0
    )

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

    global current_candle
    global current_bucket

    # ========================================================
    # JSON SAFETY
    # ========================================================

    try:

        if not message:
            return

        data = json.loads(message)

    except json.JSONDecodeError:
        print("\nNON JSON MESSAGE:")
        print(message)
        return

    except Exception as e:
        print("\nJSON ERROR:")
        print(e)
        return

    # ========================================================
    # PROCESS DATA
    # ========================================================

    try:

        # only chainlink feed
        if data.get("topic") != "crypto_prices_chainlink":
            return

        payload = data.get("payload", {})

        symbol = payload.get("symbol", "").lower()

        # only BTC
        if symbol != TARGET_SYMBOL:
            return

        price = float(payload.get("value"))

        timestamp = payload.get("timestamp")

        dt = datetime.utcfromtimestamp(timestamp / 1000)

        bucket = get_5m_bucket(dt)

        # ====================================================
        # NEW CANDLE START
        # ====================================================

        if current_bucket != bucket:

            # print previous candle
            if current_candle is not None:

                direction = "UP"

                if current_candle["close"] < current_candle["open"]:
                    direction = "DOWN"

                elif current_candle["close"] == current_candle["open"]:
                    direction = "FLAT"

                print("\n================================================")
                print("5 MIN CANDLE CLOSED")
                print("================================================")
                print("TIME  :", current_bucket)
                print("OPEN  :", round(current_candle["open"], 2))
                print("HIGH  :", round(current_candle["high"], 2))
                print("LOW   :", round(current_candle["low"], 2))
                print("CLOSE :", round(current_candle["close"], 2))
                print("MOVE  :", direction)

            # create new candle
            current_bucket = bucket

            current_candle = {
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }

            print("\n------------------------------------------------")
            print("NEW 5M CANDLE STARTED")
            print("------------------------------------------------")
            print("TIME :", current_bucket)
            print("OPEN :", round(price, 2))

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

        # ====================================================
        # LIVE PRICE
        # ====================================================

        print(
            f"LIVE BTC | "
            f"{dt.strftime('%H:%M:%S')} | "
            f"{round(price, 2)}"
        )

    except Exception as e:
        print("\nPROCESSING ERROR:")
        print(e)

# ============================================================
# ERROR
# ============================================================

def on_error(ws, error):

    print("\nWEBSOCKET ERROR")
    print(error)

# ============================================================
# CLOSE
# ============================================================

def on_close(ws, close_status_code, close_msg):

    print("\n================================================")
    print("WEBSOCKET CLOSED")
    print("================================================")

    print(close_status_code)
    print(close_msg)

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("================================================")
    print("BTC 5M CANDLE LOGGER")
    print("================================================")

    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()
