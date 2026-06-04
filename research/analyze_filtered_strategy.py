import sqlite3
import pandas as pd

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql_query("""
SELECT *
FROM predictions
WHERE signal='DOWN'
""", conn)

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

good_hours = [1,3,5,6,13,15]

df = df[
    df["hour"].isin(good_hours)
]

wins = len(
    df[df["outcome"]=="WIN"]
)

losses = len(
    df[df["outcome"]=="LOSS"]
)

total = wins + losses

print("TRADES :", total)

print("WINS   :", wins)

print("LOSSES :", losses)

print(
    "WINRATE:",
    round(wins/total*100,2)
)
