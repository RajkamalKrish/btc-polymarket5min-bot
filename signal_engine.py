import sqlite3
import pandas as pd

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
# LOAD DATA
# ============================================================

query = """
SELECT *
FROM candles_5m
ORDER BY id ASC
"""

df = pd.read_sql(query, conn)

# ============================================================
# CHECK DATA
# ============================================================

if len(df) < 30:

    print("\nNot enough candle data yet.")
    print("Need at least 30 candles.")

    exit()

# ============================================================
# INDICATORS
# ============================================================

df["rsi"] = calculate_rsi(df)

df["atr"] = calculate_atr(df)

df["ema9"] = calculate_ema(df, 9)

df["ema21"] = calculate_ema(df, 21)

# ============================================================
# LATEST CANDLE
# ============================================================

latest = df.iloc[-1]

signal = "SKIP"

confidence = 0.50

# ============================================================
# SIGNAL LOGIC
# ============================================================

# bullish trend
if (
    latest["close"] > latest["ema9"]
    and latest["ema9"] > latest["ema21"]
    and latest["rsi"] > 55
    and latest["atr"] > 20
):

    signal = "UP"

    confidence = 0.62

# bearish trend
elif (
    latest["close"] < latest["ema9"]
    and latest["ema9"] < latest["ema21"]
    and latest["rsi"] < 45
    and latest["atr"] > 20
):

    signal = "DOWN"

    confidence = 0.62

# ============================================================
# STORE PREDICTION
# ============================================================

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

    latest["candle_time"],

    signal,

    confidence,

    prediction_time
))

conn.commit()

# ============================================================
# OUTPUT
# ============================================================

print("\n================================================")
print("BTC SIGNAL ENGINE")
print("================================================")

print("TIME       :", latest["candle_time"])

print("CLOSE      :", round(latest["close"], 2))

print("RSI        :", round(latest["rsi"], 2))

print("ATR        :", round(latest["atr"], 2))

print("EMA9       :", round(latest["ema9"], 2))

print("EMA21      :", round(latest["ema21"], 2))

print("SIGNAL     :", signal)

print("CONFIDENCE :", confidence)

print("\nPrediction stored.")
