import sqlite3
import pandas as pd

GOOD_HOURS = [1, 3, 5, 6, 13, 15]

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql("""

SELECT
    signal,
    outcome,
    rsi,
    prediction_time

FROM predictions

WHERE
    signal='DOWN'
    AND outcome IN ('WIN','LOSS')
    AND rsi IS NOT NULL

""", conn)

conn.close()

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

df = df[
    df["hour"].isin(GOOD_HOURS)
]

bins = [0, 30, 40, 50, 60, 70, 100]

labels = [
    "0-30",
    "30-40",
    "40-50",
    "50-60",
    "60-70",
    "70+"
]

df["bucket"] = pd.cut(
    df["rsi"],
    bins=bins,
    labels=labels
)

print("\n" + "=" * 70)
print("DOWN + GOOD HOURS + RSI")
print("=" * 70)

for bucket in labels:

    subset = df[
        df["bucket"] == bucket
    ]

    trades = len(subset)

    if trades < 10:
        continue

    wins = len(
        subset[
            subset["outcome"] == "WIN"
        ]
    )

    losses = len(
        subset[
            subset["outcome"] == "LOSS"
        ]
    )

    wr = round(
        wins / trades * 100,
        2
    )

    print(
        f"{bucket:>6} | "
        f"Trades: {trades:>4} | "
        f"Wins: {wins:>4} | "
        f"Losses: {losses:>4} | "
        f"WinRate: {wr}%"
    )
