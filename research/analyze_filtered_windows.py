import sqlite3
import pandas as pd

DB = "../btc_bot.db"

GOOD_HOURS = [1, 3, 5, 6, 13, 15]

conn = sqlite3.connect(DB)

windows = [
    ("Last 250", 250),
    ("Last 500", 500),
    ("Last 1000", 1000),
    ("All Trades", None)
]

print("\n" + "=" * 70)
print("FILTERED STRATEGY VALIDATION")
print("DOWN + HOURS [1,3,5,6,13,15]")
print("=" * 70)

for name, limit in windows:

    if limit is None:

        query = """
        SELECT *
        FROM predictions
        WHERE signal IN ('UP','DOWN')
        AND outcome IN ('WIN','LOSS')
        """

    else:

        query = f"""
        SELECT *
        FROM (
            SELECT *
            FROM predictions
            WHERE signal IN ('UP','DOWN')
            AND outcome IN ('WIN','LOSS')
            ORDER BY id DESC
            LIMIT {limit}
        )
        """

    df = pd.read_sql_query(query, conn)

    df["prediction_time"] = pd.to_datetime(
        df["prediction_time"]
    )

    df["hour"] = df["prediction_time"].dt.hour

    filtered = df[
        (df["signal"] == "DOWN")
        &
        (df["hour"].isin(GOOD_HOURS))
    ]

    wins = len(
        filtered[filtered["outcome"] == "WIN"]
    )

    losses = len(
        filtered[filtered["outcome"] == "LOSS"]
    )

    total = wins + losses

    if total == 0:

        print(f"\n{name}")
        print("No trades found")
        continue

    winrate = round(
        wins / total * 100,
        2
    )

    print(f"\n{name}")
    print("-" * 30)
    print(f"Trades   : {total}")
    print(f"Wins     : {wins}")
    print(f"Losses   : {losses}")
    print(f"Win Rate : {winrate}%")

conn.close()
