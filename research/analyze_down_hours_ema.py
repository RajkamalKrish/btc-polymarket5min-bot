import sqlite3
import pandas as pd

GOOD_HOURS = [1, 3, 5, 6, 13, 15]

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql("""

SELECT
    signal,
    outcome,
    ema9,
    ema21,
    prediction_time

FROM predictions

WHERE
    signal='DOWN'
    AND outcome IN ('WIN','LOSS')
    AND ema9 IS NOT NULL
    AND ema21 IS NOT NULL

""", conn)

conn.close()

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

df = df[
    df["hour"].isin(GOOD_HOURS)
]

# =====================================================
# EMA SPREAD
# =====================================================

df["ema_spread"] = abs(
    df["ema9"] - df["ema21"]
)

median_spread = df["ema_spread"].median()

print("\n" + "=" * 70)
print("DOWN + GOOD HOURS + EMA SPREAD")
print("=" * 70)

print(
    f"\nMedian EMA Spread: "
    f"{round(median_spread, 2)}\n"
)

for label, subset in [

    (
        "LOW SPREAD",
        df[df["ema_spread"] <= median_spread]
    ),

    (
        "HIGH SPREAD",
        df[df["ema_spread"] > median_spread]
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

    print(label)
    print("-" * 30)
    print("Trades  :", trades)
    print("Wins    :", wins)
    print("Losses  :", losses)
    print("WinRate :", wr, "%")
    print()
