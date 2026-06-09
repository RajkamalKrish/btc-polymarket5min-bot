import sqlite3
import pandas as pd

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql("""

SELECT
signal,
outcome,
rsi

FROM predictions

WHERE
rsi IS NOT NULL
AND outcome IN ('WIN','LOSS')

""", conn)

conn.close()

bins = [0,30,40,50,60,70,100]

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

print("\nRSI ANALYSIS\n")

for bucket in labels:

    subset = df[
        df["bucket"] == bucket
    ]

    trades = len(subset)

    if trades == 0:
        continue

    wins = len(
        subset[
            subset["outcome"]=="WIN"
        ]
    )

    wr = round(
        wins / trades * 100,
        2
    )

    print(
        bucket,
        "Trades:",
        trades,
        "WinRate:",
        wr
    )
