import websocket
import json

WS_URL = "wss://ws-live-data.polymarket.com"

# ============================================================
# ON OPEN
# ============================================================

def on_open(ws):
    print("\nCONNECTED TO POLYMARKET RTDS")

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

    print("SUBSCRIBED TO CHAINLINK BTC FEED")

# ============================================================
# ON MESSAGE
# ============================================================

def on_message(ws, message):

    print("\nRAW:")
    print(message)

    try:
        data = json.loads(message)

        # BTC PRICE UPDATE FORMAT
        #
        # {
        #   "topic":"crypto_prices_chainlink",
        #   "type":"update",
        #   "timestamp":1753314088421,
        #   "payload":{
        #       "symbol":"btc/usd",
        #       "timestamp":1753314088395,
        #       "value":67234.50
        #   }
        # }

        if data.get("topic") == "crypto_prices_chainlink":

            payload = data.get("payload", {})

            symbol = payload.get("symbol")
            price = payload.get("value")

            print("\n============================")
            print("BTC PRICE UPDATE")
            print("============================")
            print("SYMBOL:", symbol)
            print("PRICE :", price)

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
