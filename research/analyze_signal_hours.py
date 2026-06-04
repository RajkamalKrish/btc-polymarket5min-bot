import sqlite3
import pandas as pd

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql_query("""

SELECT *
FROM predictions
WHERE signal IN ('UP','DOWN')

""", conn)

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

for signal in ["UP", "DOWN"]:

    print("\n")
    print("=" * 50)
    print(signal)
    print("=" * 50)

    signal_df = df[df["signal"] == signal]

    results = []

    for hour in range(24):

        subset = signal_df[
            signal_df["hour"] == hour
        ]

        wins = len(
            subset[subset["outcome"] == "WIN"]
        )

        losses = len(
            subset[subset["outcome"] == "LOSS"]
        )

        total = wins + losses

        if total < 20:
            continue

        winrate = wins / total * 100

        results.append(
            [hour, total, round(winrate, 2)]
        )

    results = pd.DataFrame(
        results,
        columns=[
            "hour",
            "trades",
            "winrate"
        ]
    )

    print(
        results.sort_values(
            "winrate",
            ascending=False
        )
    )
