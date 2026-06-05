import sqlite3
import pandas as pd
import time

from datetime import datetime

from indicators import (
    calculate_rsi,
    calculate_atr,
    calculate_ema
)

DB_NAME = "btc_bot.db"

conn = sqlite3.connect(DB_NAME)

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

    return (next_time - now).total_seconds()


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

    return next_time.strftime("%Y-%m-%d %H:%M:%S")


def generate_signal():

    df = pd.read_sql(
        "SELECT * FROM candles_5m ORDER BY id ASC",
        conn
    )

    if len(df) < 30:
        return

    df["rsi"] = calculate_rsi(df)
    df["atr"] = calculate_atr(df)
    df["ema9"] = calculate_ema(df, 9)
    df["ema21"] = calculate_ema(df, 21)

    latest = df.iloc[-1]

    signal = "SKIP"
    confidence = 0.50

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

    prediction_time = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO predictions
        (
            prediction_time,
            candle_time,
            signal,
            confidence,
            rsi,
            atr,
            ema9,
            ema21,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prediction_time,
            get_next_candle_time(),
            signal,
            confidence,
            float(latest["rsi"]),
            float(latest["atr"]),
            float(latest["ema9"]),
            float(latest["ema21"]),
            prediction_time
        )
    )

    conn.commit()

    print(
        prediction_time,
        signal,
        round(float(latest["rsi"]), 2)
    )


print("LIVE POLYMARKET PREDICTOR")

while True:

    try:

        seconds = seconds_until_next_5m()

        if 10 <= seconds <= 15:

            generate_signal()

            time.sleep(20)

        else:

            time.sleep(1)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(5)
