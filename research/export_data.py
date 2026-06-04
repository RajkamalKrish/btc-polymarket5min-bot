import sqlite3
import pandas as pd

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql_query("""
SELECT *
FROM predictions
WHERE signal IN ('UP','DOWN')
""", conn)

df.to_csv("predictions_export.csv", index=False)

print(df.shape)
