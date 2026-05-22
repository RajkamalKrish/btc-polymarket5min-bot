# btc_5m_sqlite_logger.py

import websocket
import json
import sqlite3
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

WS_URL = "wss://ws-live-data.polymarket.com"

TARGET_SYMBOL = "btc/usd"

DB_NAME = "btc_bot.db"

# ============================================================
# SQLITE SETUP
# ============================================================

conn = sqlite3.connect(DB_NAME, check_same_thread=False)

cursor = conn.cursor()

# ============================================================
# CREATE TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS candles_5m (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    candle_time TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,

    direction TEXT,

    range_value REAL,
    body_size REAL,

    created_at TEXT
)
""")

conn.commit()

# ============================================================
# GLOBALS
# ============================================================

current_candle = None
current_bucket = None

# ============================================================
# HELPERS
# ============================================================

def get_5m_bucket(dt):

    minute = (dt.minute // 5) * 5

    return dt.replace(
        minute=minute,
        second=0,
        microsecond=0
    )

# ============================================================
# SAVE CANDLE
# ============================================================

def save_candle(bucket, candle):

    direction = "UP"

    if candle["close"] < candle["open"]:
        direction = "DOWN"

    elif candle["close"] == candle["open"]:
        direction = "FLAT"

    range_value = candle["high"] - candle["low"]

    body_size = abs(
        candle["close"] - candle["open"]
    )

    cursor.execute("""
    INSERT INTO candles_5m (

        candle_time,
        open,
        high,
        low,
        close,

        direction,

        range_value,
        body_size,

        created_at

    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        str(bucket),

        candle["open"],
        candle["high"],
        candle["low"],
        candle["close"],

        direction,

        range_value,
        body_size,

        datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()

    print("\n================================================")
    print("5M CANDLE SAVED TO SQLITE")
    print("================================================")

    print("TIME      :", bucket)
    print("OPEN      :", round(candle["open"], 2))
    print("HIGH      :", round(candle["high"], 2))
    print("LOW       :", round(candle["low"], 2))
    print("CLOSE     :", round(candle["close"], 2))
    print("DIRECTION :", direction)

# ============================================================
# OPEN
# ============================================================

def on_open(ws):

    print("================================================")
    print("BTC SQLITE LOGGER STARTED")
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

    print("\nSubscribed to BTC feed")

# ============================================================
# MESSAGE
# ============================================================

def on_message(ws, message):

    global current_candle
    global current_bucket

    # ========================================================
    # SAFE JSON PARSE
    # ========================================================

    try:

        if not message:
            return

        data = json.loads(message)

    except:
        return

    try:

        # only chainlink feed
        if data.get("topic") != "crypto_prices_chainlink":
            return

        payload = data.get("payload", {})

        symbol = payload.get(
            "symbol",
            ""
        ).lower()

        # only BTC
        if symbol != TARGET_SYMBOL:
            return

        price = float(
            payload.get("value")
        )

        timestamp = payload.get(
            "timestamp"
        )

        dt = datetime.utcfromtimestamp(
            timestamp / 1000
        )

        bucket = get_5m_bucket(dt)

        # ====================================================
        # NEW CANDLE
        # ====================================================

        if current_bucket != bucket:

            # save previous candle
            if current_candle is not None:

                save_candle(
                    current_bucket,
                    current_candle
                )

            # start new candle
            current_bucket = bucket

            current_candle = {
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }

            print("\n------------------------------------------------")
            print("NEW 5M CANDLE")
            print("------------------------------------------------")
            print("TIME :", current_bucket)
            print("OPEN :", round(price, 2))

        # ====================================================
        # UPDATE CURRENT CANDLE
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

        print("PROCESSING ERROR:", e)

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

    print("\nWEBSOCKET CLOSED")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()
