# polymarket_chainlink_logger.py

import websocket
import json
import threading
import time
import sqlite3
from datetime import datetime
from collections import deque

# ============================================================
# CONFIG
# ============================================================

WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws"

DB_NAME = "btc_chainlink.db"

SAVE_RAW_MESSAGES = True

# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS btc_ticks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    asset TEXT,
    price REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS raw_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    message TEXT
)
""")

conn.commit()

# ============================================================
# MEMORY
# ============================================================

price_buffer = deque(maxlen=300)

latest_price = None

# ============================================================
# HELPERS
# ============================================================

def now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def save_tick(asset, price):
    cursor.execute("""
    INSERT INTO btc_ticks (timestamp, asset, price)
    VALUES (?, ?, ?)
    """, (now(), asset, price))
    conn.commit()

def save_raw(message):
    cursor.execute("""
    INSERT INTO raw_messages (timestamp, message)
    VALUES (?, ?)
    """, (now(), message))
    conn.commit()

# ============================================================
# ANALYTICS
# ============================================================

def calculate_momentum():
    if len(price_buffer) < 20:
        return 0

    old_price = price_buffer[0]
    new_price = price_buffer[-1]

    return new_price - old_price

def calculate_volatility():
    if len(price_buffer) < 20:
        return 0

    prices = list(price_buffer)

    returns = []

    for i in range(1, len(prices)):
        returns.append(abs(prices[i] - prices[i - 1]))

    return sum(returns) / len(returns)

def print_stats():
    global latest_price

    while True:
        time.sleep(5)

        if latest_price is None:
            continue

        momentum = calculate_momentum()
        volatility = calculate_volatility()

        signal = "SKIP"

        if momentum > 20:
            signal = "UP"

        elif momentum < -20:
            signal = "DOWN"

        print("\n================================================")
        print("LIVE BTC ANALYSIS")
        print("================================================")
        print("TIME:", now())
        print("PRICE:", latest_price)
        print("MOMENTUM:", round(momentum, 2))
        print("VOLATILITY:", round(volatility, 2))
        print("SIGNAL:", signal)

# ============================================================
# WEBSOCKET EVENTS
# ============================================================

def on_open(ws):
    print("\n================================================")
    print("CONNECTED TO POLYMARKET LIVE DATA")
    print("================================================")

    subscribe_msg = {
        "type": "subscribe",
        "channel": "crypto_prices_chainlink"
    }

    ws.send(json.dumps(subscribe_msg))

    print("\nSubscribed to:")
    print("crypto_prices_chainlink")

def on_message(ws, message):
    global latest_price

    try:
        print("\nRAW MESSAGE:")
        print(message)

        if SAVE_RAW_MESSAGES:
            save_raw(message)

        data = json.loads(message)

        # ----------------------------------------------------
        # EXPECTED FORMAT
        # ----------------------------------------------------
        #
        # {
        #   "channel":"crypto_prices_chainlink",
        #   "data":{
        #       "asset":"BTC",
        #       "price":108245.23,
        #       "timestamp":"..."
        #   }
        # }
        #
        # ----------------------------------------------------

        if "data" not in data:
            return

        tick = data["data"]

        asset = tick.get("asset")
        price = tick.get("price")

        if asset is None or price is None:
            return

        latest_price = float(price)

        price_buffer.append(latest_price)

        save_tick(asset, latest_price)

        print("\nBTC TICK SAVED")
        print("ASSET:", asset)
        print("PRICE:", latest_price)

    except Exception as e:
        print("\nERROR PROCESSING MESSAGE")
        print(str(e))

def on_error(ws, error):
    print("\nWEBSOCKET ERROR")
    print(error)

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

    print("============================================================")
    print("POLYMARKET CHAINLINK LOGGER")
    print("============================================================")

    threading.Thread(target=print_stats, daemon=True).start()

    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()
