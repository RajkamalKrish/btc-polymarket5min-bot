import sqlite3
import pandas as pd

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql_query("""

SELECT *
FROM predictions

WHERE signal='DOWN'
AND outcome IN ('WIN','LOSS')

""", conn)

conn.close()

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

good_hours = [1,3,5,6,13,15]

df = df[
    df["hour"].isin(good_hours)
]

median_conf = df["confidence"].median()

print("\n" + "="*70)
print("CONFIDENCE ANALYSIS")
print("="*70)

print(
    "\nMedian Confidence:",
    median_conf
)

for label, subset in [

    (
        "LOW CONFIDENCE",
        df[
            df["confidence"] <= median_conf
        ]
    ),

    (
        "HIGH CONFIDENCE",
        df[
            df["confidence"] > median_conf
        ]
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
    print("-"*30)
    print("Trades :", total)
    print("Wins   :", wins)
    print("Losses :", losses)
    print(
        "WinRate:",
        round(wins/total*100,2),
        "%"
    )
