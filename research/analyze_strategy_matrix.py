import sqlite3
import pandas as pd

# ============================================================
# LOAD DATA
# ============================================================

conn = sqlite3.connect("../btc_bot.db")

df = pd.read_sql("""

SELECT
    signal,
    outcome,
    prediction_time,
    rsi,
    atr,
    ema9,
    ema21

FROM predictions

WHERE
    outcome IN ('WIN','LOSS')
    AND rsi IS NOT NULL
    AND atr IS NOT NULL
    AND ema9 IS NOT NULL
    AND ema21 IS NOT NULL

""", conn)

conn.close()

# ============================================================
# FEATURES
# ============================================================

df["prediction_time"] = pd.to_datetime(
    df["prediction_time"]
)

df["hour"] = df["prediction_time"].dt.hour

# EMA spread

df["ema_spread"] = abs(
    df["ema9"] - df["ema21"]
)

# ============================================================
# RSI BUCKETS
# ============================================================

df["rsi_bucket"] = pd.cut(

    df["rsi"],

    bins=[0,30,40,50,60,70,100],

    labels=[
        "0-30",
        "30-40",
        "40-50",
        "50-60",
        "60-70",
        "70+"
    ]
)

# ============================================================
# ATR BUCKETS
# ============================================================

atr_median = df["atr"].median()

df["atr_bucket"] = df["atr"].apply(

    lambda x:
    "HIGH_ATR"
    if x > atr_median
    else "LOW_ATR"
)

# ============================================================
# EMA SPREAD BUCKETS
# ============================================================

spread_median = df["ema_spread"].median()

df["spread_bucket"] = df["ema_spread"].apply(

    lambda x:
    "HIGH_SPREAD"
    if x > spread_median
    else "LOW_SPREAD"
)

# ============================================================
# STRATEGY MATRIX
# ============================================================

results = []

grouped = df.groupby([

    "signal",
    "hour",
    "rsi_bucket",
    "atr_bucket",
    "spread_bucket"

])

for name, subset in grouped:

    trades = len(subset)

    # -----------------------------------------
    # Ignore tiny samples
    # -----------------------------------------

    if trades < 20:
        continue

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

    results.append({

        "signal": name[0],

        "hour": name[1],

        "rsi_bucket": name[2],

        "atr_bucket": name[3],

        "spread_bucket": name[4],

        "trades": trades,

        "wins": wins,

        "losses": losses,

        "winrate": winrate

    })

# ============================================================
# OUTPUT
# ============================================================

results = pd.DataFrame(results)

if len(results) == 0:

    print(
        "\nNo combinations "
        "found with >= 20 trades."
    )

    quit()

results = results.sort_values(

    by="winrate",

    ascending=False

)

print("\n" + "=" * 90)
print("TOP STRATEGY COMBINATIONS")
print("=" * 90)

print(
    results.head(50).to_string(
        index=False
    )
)

# ============================================================
# SAVE CSV
# ============================================================

results.to_csv(

    "strategy_matrix.csv",

    index=False

)

print(
    "\nSaved: strategy_matrix.csv"
)
