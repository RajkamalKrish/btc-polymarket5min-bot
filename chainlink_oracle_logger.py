import csv
import json
import time
from datetime import datetime

import websocket

# =====================================================
# CONFIG
# =====================================================

CSV_FILE = "chainlink_btc_prices.csv"

WS_URL = (
    "wss://ws-subscriptions-clob.polymarket.com/ws/"
)

# =====================================================
# CSV SETUP
# =====================================================

def setup_csv():

    try:

        with open(
            CSV_FILE,
            "x",
            newline=""
        ) as f:

            writer = csv.writer(f)

            writer.writerow([

                "local_timestamp",

                "oracle_timestamp",

                "btc_price"

            ])

    except FileExistsError:
        pass

# =====================================================
# SAVE PRICE
# =====================================================

def save_price(
    oracle_ts,
    btc_price
):

    with open(
        CSV_FILE,
        "a",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow([

            datetime.utcnow()
            .isoformat(),

            oracle_ts,

            btc_price

        ])

# =====================================================
# MESSAGE HANDLER
# =====================================================

def on_message(
    ws,
    message
):

    try:

        data = json.loads(message)

        topic = data.get("topic")

        if (
            topic
            != "crypto_prices_chainlink"
        ):

            return

        payload = data.get(
            "payload",
            {}
        )

        symbol = payload.get(
            "symbol",
            ""
        ).lower()

        if symbol != "btc/usd":

            return

        full_value = payload.get(
            "full_accuracy_value"
        )

        oracle_ts = payload.get(
            "timestamp"
        )

        if (
            not full_value
            or
            not oracle_ts
        ):

            return

        # =========================================
        # CONVERT 18-DECIMAL FIXED POINT
        # =========================================

        btc_price = (
            int(full_value)
            / 1e18
        )

        print()

        print("=" * 60)

        print(
            "CHAINLINK BTC UPDATE"
        )

        print(
            f"Oracle TS: "
            f"{oracle_ts}"
        )

        print(
            f"BTC/USD: "
            f"{btc_price:,.2f}"
        )

        print("=" * 60)

        # =========================================
        # SAVE
        # =========================================

        save_price(
            oracle_ts,
            btc_price
        )

    except Exception as e:

        print(
            f"Message error: {e}"
        )

# =====================================================
# ERROR HANDLER
# =====================================================

def on_error(
    ws,
    error
):

    print(
        f"WebSocket error: {error}"
    )

# =====================================================
# CLOSE HANDLER
# =====================================================

def on_close(
    ws,
    close_status_code,
    close_msg
):

    print()

    print("=" * 60)

    print(
        "WebSocket closed"
    )

    print("=" * 60)

# =====================================================
# OPEN HANDLER
# =====================================================

def on_open(ws):

    print()

    print("=" * 60)

    print(
        "CONNECTED TO "
        "POLYMARKET CHAINLINK FEED"
    )

    print("=" * 60)

    # =============================================
    # SUBSCRIBE
    # =============================================

    subscribe_msg = {

        "type":
            "subscribe",

        "topic":
            "crypto_prices_chainlink"

    }

    ws.send(
        json.dumps(subscribe_msg)
    )

    print()

    print(
        "Subscribed to:"
    )

    print(
        "crypto_prices_chainlink"
    )

    print()

# =====================================================
# MAIN
# =====================================================

def main():

    setup_csv()

    print("=" * 60)

    print(
        "POLYMARKET "
        "CHAINLINK LOGGER"
    )

    print("=" * 60)

    while True:

        try:

            ws = websocket.WebSocketApp(

                WS_URL,

                on_open=on_open,

                on_message=on_message,

                on_error=on_error,

                on_close=on_close

            )

            ws.run_forever()

        except KeyboardInterrupt:

            print()

            print(
                "Stopping logger..."
            )

            break

        except Exception as e:

            print(
                f"Reconnect error: {e}"
            )

            time.sleep(5)

# =====================================================
# START
# =====================================================

if __name__ == "__main__":

    main()
