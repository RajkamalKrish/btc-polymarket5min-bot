import pandas as pd
import requests
import time

SIGNALS_FILE = "signals.csv"
OUTPUT_FILE = "resolved_signals.csv"

FEE_RATE = 0.10

print("=" * 60)
print("RESOLVING SIGNAL OUTCOMES")
print("=" * 60)

# ======================================================
# LOAD SIGNALS
# ======================================================

signals = pd.read_csv(SIGNALS_FILE)

signals.columns = (
    signals.columns
    .str.strip()
)

resolved_rows = []

# ======================================================
# RESOLVE EACH MARKET
# ======================================================

for idx, row in signals.iterrows():

    slug = row["market_slug"]

    signal = row["signal"]

    yes_price = float(
        row["yes_price"]
    )

    no_price = float(
        row["no_price"]
    )

    print(f"\nChecking: {slug}")

    url = (
        "https://gamma-api.polymarket.com/markets"
        f"?slug={slug}"
    )

    try:

        r = requests.get(
            url,
            timeout=10
        )

        data = r.json()

        if not data:

            print("No market data")
            continue

        market = data[0]

        closed = market.get(
            "closed",
            False
        )

        if not closed:

            print("Still open")
            continue

        outcome = market.get(
            "outcome",
            ""
        )

        winner = outcome.upper()

        # ==========================================
        # DETERMINE WIN / LOSS
        # ==========================================

        if signal == "BUY_YES":

            won = (
                winner == "YES"
            )

            entry_price = yes_price

        else:

            won = (
                winner == "NO"
            )

            entry_price = no_price

        # ==========================================
        # PNL
        # ==========================================

        if won:

            pnl = (
                (1 - entry_price)
                * (1 - FEE_RATE)
            )

            result = "WIN"

        else:

            pnl = -entry_price

            result = "LOSS"

        print(
            f"{signal} → {result}"
        )

        resolved_rows.append({

            "timestamp":
                row["timestamp"],

            "market_slug":
                slug,

            "signal":
                signal,

            "yes_price":
                yes_price,

            "no_price":
                no_price,

            "divergence":
                row["divergence"],

            "momentum_pct":
                row["momentum_pct"],

            "result":
                result,

            "winner":
                winner,

            "pnl":
                round(pnl, 4)

        })

        time.sleep(0.2)

    except Exception as e:

        print(f"Error: {e}")

# ======================================================
# SAVE
# ======================================================

resolved_df = pd.DataFrame(
    resolved_rows
)

resolved_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 60)

print(
    f"Resolved trades: "
    f"{len(resolved_df)}"
)

print(
    f"Saved to: "
    f"{OUTPUT_FILE}"
)

print("=" * 60)
