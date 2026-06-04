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

def session(hour):

    if 0 <= hour < 8:
        return "ASIA"

    elif 8 <= hour < 16:
        return "LONDON"

    return "US"

df["session"] = (
    df["prediction_time"]
    .dt.hour
    .apply(session)
)

for s in ["ASIA","LONDON","US"]:

    subset = df[df["session"] == s]

    wins = len(
        subset[subset["outcome"]=="WIN"]
    )

    losses = len(
        subset[subset["outcome"]=="LOSS"]
    )

    total = wins + losses

    wr = wins/total*100

    print(
        s,
        total,
        round(wr,2)
    )
