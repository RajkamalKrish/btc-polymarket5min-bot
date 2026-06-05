import sqlite3
import pandas as pd

DB = "../btc_bot.db"

GOOD_HOURS = [1, 3, 5, 6, 13, 15]

conn = sqlite3.connect(DB)

# ==========================================================
# LOAD DATA
# ==========================================================

query = """
SELECT
    p.id,
    p.prediction_time,
    p.candle_time,
    p.signal,
    p.outcome,
    c.range_value,
    c.body_size

FROM predictions p

JOIN candles_5m c
ON p.candle_time = c.candle_time

WHERE
    p.signal = 'DOWN'
    AND p.outcome IN ('WIN', 'LOSS')
"""

df = pd.read_sql_query(query, conn)

conn.close()

# ==========================================================
# FILTER HOURS
# ==========================================================

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

df = df[
    df["hour"].isin(GOOD_HOURS)
]

# ==========================================================
# MEDIAN RANGE
# ==========================================================

median_range = df["range_value"].median()

print("\n" + "=" * 70)
print("RANGE FILTER ANALYSIS")
print("=" * 70)

print(
    f"\nMedian Range Value: "
    f"{round(median_range, 2)}"
)

# ==========================================================
# LOW RANGE
# ==========================================================

low_range = df[
    df["range_value"] <= median_range
]

wins = len(
    low_range[low_range["outcome"] == "WIN"]
)

losses = len(
    low_range[low_range["outcome"] == "LOSS"]
)

total = wins + losses

if total > 0:

    winrate = wins / total * 100

    print("\nLOW RANGE")
    print("-" * 30)
    print("Trades  :", total)
    print("Wins    :", wins)
    print("Losses  :", losses)
    print(
        "WinRate :",
        round(winrate, 2),
        "%"
    )

# ==========================================================
# HIGH RANGE
# ==========================================================

high_range = df[
    df["range_value"] > median_range
]

wins = len(
    high_range[high_range["outcome"] == "WIN"]
)

losses = len(
    high_range[high_range["outcome"] == "LOSS"]
)

total = wins + losses

if total > 0:

    winrate = wins / total * 100

    print("\nHIGH RANGE")
    print("-" * 30)
    print("Trades  :", total)
    print("Wins    :", wins)
    print("Losses  :", losses)
    print(
        "WinRate :",
        round(winrate, 2),
        "%"
    )
