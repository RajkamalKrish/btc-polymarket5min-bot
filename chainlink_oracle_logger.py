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
    "wss://ws-live-data.polymarket.com/"
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

        # =============================================
        # DEBUG
        # =============================================

        print()

        print("RAW MESSAGE:")
        print(data)

        # =============================================
        # ONLY CHAINLINK STREAM
        # =============================================

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

        # =============================================
        # CONVERT 18 DECIMAL
        # =============================================

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

        save_price(
            oracle_ts,
            btc_price
        )

    except Exception as e:

        print(
            f"Message error: {e}"
        )

# =====================================================
# ERROR
# =====================================================

def on_error(
    ws,
    error
):

    print()

    print("=" * 60)

    print(
        f"WebSocket error: {error}"
    )

    print("=" * 60)

# =====================================================
# CLOSE
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
# OPEN
# =====================================================

def on_open(ws):

    print()

    print("=" * 60)

    print(
        "CONNECTED TO "
        "POLYMARKET LIVE DATA"
    )

    print("=" * 60)

    # =============================================
    # CORRECT PM SUBSCRIPTION FORMAT
    # =============================================

    subscribe_msg = {

        "action": "subscribe",

        "subscriptions": [

            {
                "topic":
                    "crypto_prices_chainlink"
            }

        ]

    }

    ws.send(
        json.dumps(
            subscribe_msg
        )
    )

    print()

    print(
        "Subscribed to:"
    )

    print(
        "crypto_prices_chainlink"
    )

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

            print()

            print("=" * 60)

            print(
                f"Reconnect error: {e}"
            )

            print(
                "Retrying in 5s..."
            )

            print("=" * 60)

            time.sleep(5)

# =====================================================
# START
# =====================================================

if __name__ == "__main__":

    main()
