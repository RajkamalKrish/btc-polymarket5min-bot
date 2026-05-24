# live_polymarket_predictor.py

import sqlite3
import pandas as pd
import time

from datetime import datetime, timedelta

from indicators import (
    calculate_rsi,
    calculate_atr,
    calculate_ema
)

# ============================================================
# DATABASE
# ============================================================

DB_NAME = "btc_bot.db"

conn = sqlite3.connect(DB_NAME)

# ============================================================
# WAIT UNTIL NEXT 5M WINDOW
# ============================================================

def seconds_until_next_5m():

    now = datetime.utcnow()

    next_minute = ((now.minute // 5) + 1) * 5

    if next_minute == 60:

        next_time = now.replace(
            hour=(now.hour + 1) % 24,
            minute=0,
            second=0,
            microsecond=0
        )

    else:

        next_time = now.replace(
            minute=next_minute,
            second=0,
            microsecond=0
        )

    delta = next_time - now

    return delta.total_seconds()

# ============================================================
# GET NEXT CANDLE TIME
# ============================================================

def get_next_candle_time():

    now = datetime.utcnow()

    next_minute = ((now.minute // 5) + 1) * 5

    if next_minute == 60:

        next_time = now.replace(
            hour=(now.hour + 1) % 24,
            minute=0,
            second=0,
            microsecond=0
        )

    else:

        next_time = now.replace(
            minute=next_minute,
            second=0,
            microsecond=0
        )

    return next_time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

# ============================================================
# GENERATE SIGNAL
# ============================================================

def generate_signal():

    query = """
    SELECT *
    FROM candles_5m
    ORDER BY id ASC
    """

    df = pd.read_sql(query, conn)

    if len(df) < 30:

        print("Not enough candles yet.")

        return

    # ========================================================
    # INDICATORS
    # ========================================================

    df["rsi"] = calculate_rsi(df)

    df["atr"] = calculate_atr(df)

    df["ema9"] = calculate_ema(df, 9)

    df["ema21"] = calculate_ema(df, 21)

    latest = df.iloc[-1]

    signal = "SKIP"

    confidence = 0.50

    # ========================================================
    # SIGNAL LOGIC
    # ========================================================

    if (
        latest["close"] > latest["ema9"]
        and latest["ema9"] > latest["ema21"]
        and latest["rsi"] > 55
        and latest["atr"] > 20
    ):

        signal = "UP"

        confidence = 0.62

    elif (
        latest["close"] < latest["ema9"]
        and latest["ema9"] < latest["ema21"]
        and latest["rsi"] < 45
        and latest["atr"] > 20
    ):

        signal = "DOWN"

        confidence = 0.62

    # ========================================================
    # TARGET NEXT CANDLE
    # ========================================================

    next_candle_time = get_next_candle_time()

    prediction_time = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO predictions (

        prediction_time,
        candle_time,
        signal,
        confidence,
        created_at

    ) VALUES (?, ?, ?, ?, ?)

    """, (

        prediction_time,

        next_candle_time,

        signal,

        confidence,

        prediction_time
    ))

    conn.commit()

    # ========================================================
    # OUTPUT
    # ========================================================

    print("\n================================================")
    print("LIVE POLYMARKET PREDICTION")
    print("================================================")

    print("PREDICTION TIME :", prediction_time)

    print("TARGET CANDLE   :", next_candle_time)

    print("SIGNAL          :", signal)

    print("CONFIDENCE      :", confidence)

    print("RSI             :", round(latest["rsi"], 2))

    print("ATR             :", round(latest["atr"], 2))

    print("EMA9            :", round(latest["ema9"], 2))

    print("EMA21           :", round(latest["ema21"], 2))

# ============================================================
# MAIN LOOP
# ============================================================

print("\n================================================")
print("LIVE POLYMARKET PREDICTOR")
print("================================================")

while True:

    try:

        now = datetime.utcnow()

        seconds = seconds_until_next_5m()

        # ====================================================
        # RUN 15 SECONDS BEFORE NEXT CANDLE
        # ====================================================

        if 10 <= seconds <= 15:

            generate_signal()

            # avoid duplicate prediction
            time.sleep(20)

        else:

            print(
                f"UTC TIME: {now.strftime('%H:%M:%S')} | "
                f"SECONDS TO NEXT 5M: {round(seconds)}",
                end="\r"
            )

            time.sleep(1)

    except Exception as e:

        print("\nERROR:", e)

        time.sleep(5)
