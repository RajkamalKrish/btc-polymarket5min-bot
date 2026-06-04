
import sqlite3
import pandas as pd

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql_query("""

SELECT *
FROM predictions
WHERE signal IN ('UP','DOWN')
AND outcome IN ('WIN','LOSS')
ORDER BY id DESC
LIMIT 500

""", conn)

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

good_hours = [1,3,5,6,13,15]

filtered = df[
    (df["signal"] == "DOWN")
    &
    (df["hour"].isin(good_hours))
]

wins = len(
    filtered[filtered["outcome"] == "WIN"]
)

losses = len(
    filtered[filtered["outcome"] == "LOSS"]
)

total = wins + losses

print("TRADES :", total)
print("WINS   :", wins)
print("LOSSES :", losses)

if total > 0:
    print(
        "WINRATE:",
        round(wins / total * 100, 2)
    )
