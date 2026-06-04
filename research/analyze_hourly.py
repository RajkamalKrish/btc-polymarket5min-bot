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

results = []

for hour in range(24):

    subset = df[df["hour"] == hour]

    wins = len(
        subset[subset["outcome"] == "WIN"]
    )

    losses = len(
        subset[subset["outcome"] == "LOSS"]
    )

    total = wins + losses

    if total == 0:
        continue

    winrate = wins / total * 100

    results.append(
        [hour, total, round(winrate,2)]
    )

results = pd.DataFrame(
    results,
    columns=["hour","trades","winrate"]
)

print(
    results.sort_values(
        "winrate",
        ascending=False
    )
)
