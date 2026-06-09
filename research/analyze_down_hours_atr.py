import sqlite3
import pandas as pd

GOOD_HOURS = [1, 3, 5, 6, 13, 15]

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql("""

SELECT
    signal,
    outcome,
    atr,
    prediction_time

FROM predictions

WHERE
    signal='DOWN'
    AND outcome IN ('WIN','LOSS')
    AND atr IS NOT NULL

""", conn)

conn.close()

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

df = df[
    df["hour"].isin(GOOD_HOURS)
]

median_atr = df["atr"].median()

print("\n" + "=" * 70)
print("DOWN + GOOD HOURS + ATR")
print("=" * 70)

for label, subset in [

    (
        "LOW ATR",
        df[df["atr"] <= median_atr]
    ),

    (
        "HIGH ATR",
        df[df["atr"] > median_atr]
    )

]:

    trades = len(subset)

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
        f"{label} | "
        f"Trades: {trades} | "
        f"Wins: {wins} | "
        f"Losses: {losses} | "
        f"WinRate: {wr}%"
    )
