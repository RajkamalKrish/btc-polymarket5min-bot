import sqlite3
import pandas as pd

DB = "../btc_bot.db"

GOOD_HOURS = [1, 3, 5, 6, 13, 15]

conn = sqlite3.connect(DB)

query = """
SELECT
    p.id,
    p.prediction_time,
    p.candle_time,
    p.signal,
    p.outcome,
    c.body_size

FROM predictions p

JOIN candles_5m c
ON p.candle_time = c.candle_time

WHERE
    p.signal = 'DOWN'
    AND p.outcome IN ('WIN','LOSS')
"""

df = pd.read_sql_query(query, conn)

conn.close()

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

df = df[
    df["hour"].isin(GOOD_HOURS)
]

median_body = df["body_size"].median()

print("\n" + "=" * 70)
print("BODY SIZE FILTER ANALYSIS")
print("=" * 70)

print(
    f"\nMedian Body Size: "
    f"{round(median_body,2)}"
)

for label, subset in [

    (
        "LOW BODY",
        df[df["body_size"] <= median_body]
    ),

    (
        "HIGH BODY",
        df[df["body_size"] > median_body]
    )

]:

    wins = len(
        subset[
            subset["outcome"]=="WIN"
        ]
    )

    losses = len(
        subset[
            subset["outcome"]=="LOSS"
        ]
    )

    total = wins + losses

    print("\n" + label)
    print("-" * 30)
    print("Trades  :", total)
    print("Wins    :", wins)
    print("Losses  :", losses)
    print(
        "WinRate :",
        round(wins/total*100,2),
        "%"
    )
