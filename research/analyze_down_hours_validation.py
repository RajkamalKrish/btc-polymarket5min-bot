import sqlite3
import pandas as pd

GOOD_HOURS = [1, 3, 5, 6, 13, 15]

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql("""

SELECT
    signal,
    outcome,
    prediction_time

FROM predictions

WHERE
    signal = 'DOWN'
    AND outcome IN ('WIN', 'LOSS')

ORDER BY id ASC

""", conn)

conn.close()

# =====================================================
# PREPARE DATA
# =====================================================

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

df = df[
    df["hour"].isin(GOOD_HOURS)
]

# =====================================================
# VALIDATION FUNCTION
# =====================================================

def analyze_subset(name, subset):

    trades = len(subset)

    if trades == 0:
        return

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

    winrate = round(
        wins / trades * 100,
        2
    )

    print(name)
    print("-" * 30)
    print("Trades   :", trades)
    print("Wins     :", wins)
    print("Losses   :", losses)
    print("Win Rate :", winrate, "%")
    print()

# =====================================================
# RESULTS
# =====================================================

print("\n" + "=" * 70)
print("DOWN + HOURS [1,3,5,6,13,15] VALIDATION")
print("=" * 70)
print()

analyze_subset(
    "Last 100 Trades",
    df.tail(100)
)

analyze_subset(
    "Last 250 Trades",
    df.tail(250)
)

analyze_subset(
    "Last 500 Trades",
    df.tail(500)
)

analyze_subset(
    "All Trades",
    df
)
