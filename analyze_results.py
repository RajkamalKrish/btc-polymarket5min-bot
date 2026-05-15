import pandas as pd
from pathlib import Path

# =====================================================
# FILES
# =====================================================

MARKET_FILE = "market_data.csv"
SIGNALS_FILE = "signals.csv"

OUTPUT_DIR = "analysis"

Path(OUTPUT_DIR).mkdir(
    exist_ok=True
)

# =====================================================
# LOAD DATA
# =====================================================

print()
print("=" * 60)
print("LOADING DATA")
print("=" * 60)

market_df = pd.read_csv(
    MARKET_FILE
)

print(
    f"Market rows: "
    f"{len(market_df):,}"
)

try:

    signals_df = pd.read_csv(
        SIGNALS_FILE
    )

    print(
        f"Signal rows: "
        f"{len(signals_df):,}"
    )

except Exception:

    signals_df = pd.DataFrame()

    print(
        "No signals found"
    )

# =====================================================
# CLEAN DATA
# =====================================================

market_df["timestamp"] = pd.to_datetime(
    market_df["timestamp"]
)

market_df["hour"] = (
    market_df["timestamp"]
    .dt.hour
)

# =====================================================
# BASIC STATS
# =====================================================

summary = {}

summary["total_market_rows"] = (
    len(market_df)
)

summary["total_signals"] = (
    len(signals_df)
)

summary["avg_momentum"] = round(
    market_df["momentum_pct"]
    .abs()
    .mean(),
    4
)

summary["max_momentum"] = round(
    market_df["momentum_pct"]
    .abs()
    .max(),
    4
)

summary["avg_volume_ratio"] = round(
    market_df["volume_ratio"]
    .mean(),
    4
)

summary["avg_divergence"] = round(
    market_df["divergence"]
    .mean(),
    4
)

summary["avg_yes_price"] = round(
    market_df["yes_price"]
    .mean(),
    4
)

summary["avg_time_left"] = round(
    market_df["time_left"]
    .mean(),
    2
)

# =====================================================
# SAVE SUMMARY
# =====================================================

summary_df = pd.DataFrame(
    [summary]
)

summary_path = (
    f"{OUTPUT_DIR}/summary.csv"
)

summary_df.to_csv(
    summary_path,
    index=False
)

# =====================================================
# TOP MOMENTUM EVENTS
# =====================================================

top_momentum = (
    market_df.sort_values(
        "momentum_pct",
        key=abs,
        ascending=False
    )
    .head(100)
)

top_momentum_path = (
    f"{OUTPUT_DIR}/top_momentum.csv"
)

top_momentum.to_csv(
    top_momentum_path,
    index=False
)

# =====================================================
# TOP DIVERGENCE EVENTS
# =====================================================

top_divergence = (
    market_df.sort_values(
        "divergence",
        ascending=False
    )
    .head(100)
)

top_divergence_path = (
    f"{OUTPUT_DIR}/top_divergence.csv"
)

top_divergence.to_csv(
    top_divergence_path,
    index=False
)

# =====================================================
# SIGNAL ANALYSIS
# =====================================================

if len(signals_df) > 0:

    signal_summary = {}

    signal_summary["total_signals"] = (
        len(signals_df)
    )

    signal_summary["buy_yes_signals"] = (
        (signals_df["signal"]
        == "BUY_YES")
        .sum()
    )

    signal_summary["buy_no_signals"] = (
        (signals_df["signal"]
        == "BUY_NO")
        .sum()
    )

    signal_summary["avg_signal_momentum"] = round(
        signals_df["momentum_pct"]
        .abs()
        .mean(),
        4
    )

    signal_summary["avg_signal_divergence"] = round(
        signals_df["divergence"]
        .mean(),
        4
    )

    signal_summary_df = pd.DataFrame(
        [signal_summary]
    )

    signal_summary_path = (
        f"{OUTPUT_DIR}/signal_summary.csv"
    )

    signal_summary_df.to_csv(
        signal_summary_path,
        index=False
    )

# =====================================================
# HOURLY ANALYSIS
# =====================================================

hourly_stats = (
    market_df.groupby("hour")
    .agg({
        "momentum_pct": "mean",
        "volume_ratio": "mean",
        "divergence": "mean"
    })
    .reset_index()
)

hourly_path = (
    f"{OUTPUT_DIR}/hourly_analysis.csv"
)

hourly_stats.to_csv(
    hourly_path,
    index=False
)

# =====================================================
# PRINT SUMMARY
# =====================================================

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)

for k, v in summary.items():

    print(f"{k}: {v}")

print()
print("=" * 60)
print("FILES GENERATED")
print("=" * 60)

print(summary_path)
print(top_momentum_path)
print(top_divergence_path)
print(hourly_path)

if len(signals_df) > 0:

    print(signal_summary_path)

print()
print("DONE")