import csv
import json
import time
from datetime import datetime

import requests

# =====================================================
# CONFIG
# =====================================================

LOOKBACK_MINUTES = 5

MIN_MOMENTUM_PCT = 0.30

ENTRY_THRESHOLD = 0.05

MIN_VOLUME_RATIO = 0.50

TRADE_WINDOW_SECONDS = 10

FEE_RATE = 0.10

SIGNALS_CSV = "signals.csv"

MARKET_CSV = "market_data.csv"

# =====================================================
# CSV SETUP
# =====================================================

def setup_csv():

    try:

        with open(
            MARKET_CSV,
            "x",
            newline=""
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "timestamp",
                "market_slug",
                "btc_now",
                "btc_then",
                "momentum_pct",
                "volume_ratio",
                "yes_price",
                "no_price",
                "divergence",
                "time_left"
            ])

    except FileExistsError:
        pass

    try:

        with open(
            SIGNALS_CSV,
            "x",
            newline=""
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "timestamp",
                "market_slug",
                "signal",
                "btc_now",
                "momentum_pct",
                "volume_ratio",
                "yes_price",
                "no_price",
                "divergence",
                "time_left"
            ])

    except FileExistsError:
        pass

# =====================================================
# MARKET SLUG
# =====================================================

def get_market_slug():

    ts = int(time.time())

    rounded = ts - (ts % 300)

    return (
        f"btc-updown-5m-{rounded}"
    )

# =====================================================
# TIME LEFT
# =====================================================

def get_time_left():

    ts = int(time.time())

    return 300 - (ts % 300)

# =====================================================
# FETCH POLYMARKET
# =====================================================

def fetch_market():

    slug = get_market_slug()

    url = (
        "https://gamma-api.polymarket.com/markets"
        f"?slug={slug}"
    )

    try:

        r = requests.get(
            url,
            timeout=10
        )

        if r.status_code != 200:

            return None

        data = r.json()

        if not data:

            return None

        market = data[0]

        prices = json.loads(
            market["outcomePrices"]
        )

        yes_price = float(prices[0])

        no_price = float(prices[1])

        return {
            "slug": slug,
            "yes_price": yes_price,
            "no_price": no_price,
        }

    except Exception:

        return None

# =====================================================
# BINANCE MOMENTUM
# =====================================================

def get_binance_momentum():

    url = (
        "https://api.binance.com/api/v3/klines"
        "?symbol=BTCUSDT"
        "&interval=1m"
        f"&limit={LOOKBACK_MINUTES}"
    )

    try:

        r = requests.get(
            url,
            timeout=10
        )

        candles = r.json()

        if len(candles) < 2:

            return None

        price_then = float(
            candles[0][1]
        )

        price_now = float(
            candles[-1][4]
        )

        momentum_pct = (
            (
                price_now
                - price_then
            )
            / price_then
        ) * 100

        volumes = [
            float(c[5])
            for c in candles
        ]

        avg_volume = (
            sum(volumes)
            / len(volumes)
        )

        latest_volume = volumes[-1]

        volume_ratio = (
            latest_volume
            / avg_volume
        )

        direction = (
            "up"
            if momentum_pct > 0
            else "down"
        )

        return {
            "price_now": price_now,
            "price_then": price_then,
            "momentum_pct": momentum_pct,
            "volume_ratio": volume_ratio,
            "direction": direction,
        }

    except Exception:

        return None

# =====================================================
# SIGNAL ENGINE
# =====================================================

def analyze_signal(
    momentum,
    market
):

    momentum_pct = abs(
        momentum["momentum_pct"]
    )

    if momentum_pct < MIN_MOMENTUM_PCT:

        return None, "weak momentum"

    if (
        momentum["volume_ratio"]
        < MIN_VOLUME_RATIO
    ):

        return None, "low volume"

    yes_price = market["yes_price"]

    # ============================================
    # DIRECTION
    # ============================================

    if momentum["direction"] == "up":

        signal = "BUY_YES"

        divergence = (
            0.50
            + ENTRY_THRESHOLD
            - yes_price
        )

    else:

        signal = "BUY_NO"

        divergence = (
            yes_price
            - (
                0.50
                - ENTRY_THRESHOLD
            )
        )

    # ============================================
    # MARKET ALREADY PRICED IN
    # ============================================

    if divergence <= 0:

        return None, "priced in"

    # ============================================
    # FEE FILTER
    # ============================================

    buy_price = (
        yes_price
        if signal == "BUY_YES"
        else 1 - yes_price
    )

    win_profit = (
        (1 - buy_price)
        * (1 - FEE_RATE)
    )

    breakeven = (
        buy_price
        / (
            win_profit
            + buy_price
        )
    )

    fee_penalty = (
        breakeven - 0.50
    )

    min_divergence = (
        fee_penalty + 0.02
    )

    if divergence < min_divergence:

        return None, "fees eat edge"

    return signal, divergence

# =====================================================
# LOG MARKET
# =====================================================

def log_market(
    market,
    momentum,
    divergence,
    time_left
):

    with open(
        MARKET_CSV,
        "a",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            datetime.utcnow().isoformat(),
            market["slug"],
            momentum["price_now"],
            momentum["price_then"],
            momentum["momentum_pct"],
            momentum["volume_ratio"],
            market["yes_price"],
            market["no_price"],
            divergence,
            time_left
        ])

# =====================================================
# LOG SIGNAL
# =====================================================

def log_signal(
    signal,
    market,
    momentum,
    divergence,
    time_left
):

    with open(
        SIGNALS_CSV,
        "a",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            datetime.utcnow().isoformat(),
            market["slug"],
            signal,
            momentum["price_now"],
            momentum["momentum_pct"],
            momentum["volume_ratio"],
            market["yes_price"],
            market["no_price"],
            divergence,
            time_left
        ])

# =====================================================
# MAIN
# =====================================================

def main():

    setup_csv()

    print("=" * 60)

    print(
        "BTC REPO-STYLE "
        "POLYMARKET BOT"
    )

    print("=" * 60)

    print("DRY RUN MODE")
    print()

    while True:

        try:

            market = fetch_market()

            if not market:

                print(
                    "Market fetch failed"
                )

                time.sleep(2)

                continue

            momentum = (
                get_binance_momentum()
            )

            if not momentum:

                print(
                    "Momentum fetch failed"
                )

                time.sleep(2)

                continue

            time_left = (
                get_time_left()
            )

            signal, result = (
                analyze_signal(
                    momentum,
                    market
                )
            )

            divergence = (
                result
                if isinstance(
                    result,
                    float
                )
                else 0
            )

            print()

            print(
                f"Market: "
                f"{market['slug']}"
            )

            print(
                f"BTC Now: "
                f"${momentum['price_now']:,.2f}"
            )

            print(
                f"BTC Then: "
                f"${momentum['price_then']:,.2f}"
            )

            print(
                f"Momentum: "
                f"{momentum['momentum_pct']:+.3f}%"
            )

            print(
                f"Volume Ratio: "
                f"{momentum['volume_ratio']:.2f}x"
            )

            print(
                f"Direction: "
                f"{momentum['direction']}"
            )

            print(
                f"YES Price: "
                f"{market['yes_price']:.3f}"
            )

            print(
                f"NO Price: "
                f"{market['no_price']:.3f}"
            )

            print(
                f"Time Left: "
                f"{time_left}s"
            )

            # =====================================
            # LOG EVERYTHING
            # =====================================

            log_market(
                market,
                momentum,
                divergence,
                time_left
            )

            # =====================================
            # FINAL 10 SECONDS ONLY
            # =====================================

            if (
                signal
                and
                time_left
                <= TRADE_WINDOW_SECONDS
            ):

                print()

                print("=" * 60)

                print(
                    f"SIGNAL: {signal}"
                )

                print(
                    f"DIVERGENCE: "
                    f"{divergence:.3f}"
                )

                print("=" * 60)

                print()

                log_signal(
                    signal,
                    market,
                    momentum,
                    divergence,
                    time_left
                )

            else:

                print(
                    f"Skip: {result}"
                )

            print("-" * 60)

            time.sleep(5)

        except KeyboardInterrupt:

            print(
                "Stopping bot..."
            )

            break

        except Exception as e:

            print(
                f"Error: {e}"
            )

            time.sleep(5)

# =====================================================
# START
# =====================================================

if __name__ == "__main__":

    main()