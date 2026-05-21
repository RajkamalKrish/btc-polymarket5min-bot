import csv
import json
import time
from datetime import datetime

import requests

# =====================================================
# CONFIG
# =====================================================

LOOKBACK_MINUTES = 5

MIN_MOMENTUM_PCT = 0.12
MIN_VOLUME_RATIO = 0.25

MOMENTUM_FACTOR = 0.80

MIN_DIVERGENCE_EDGE = 0.03

TRADE_WINDOW_SECONDS = 10

SIGNALS_CSV = "signals.csv"
MARKET_CSV = "market_data.csv"

# =====================================================
# CSV SETUP
# =====================================================

def setup_csv():

    # =============================================
    # MARKET DATA CSV
    # =============================================

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

                "expected_yes_price",

                "yes_price",

                "no_price",

                "divergence",

                "time_left"

            ])

    except FileExistsError:
        pass

    # =============================================
    # SIGNALS CSV
    # =============================================

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

                "expected_yes_price",

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

            "slug":
                slug,

            "yes_price":
                yes_price,

            "no_price":
                no_price

        }

    except Exception as e:

        print(
            f"Market fetch error: {e}"
        )

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

            "price_now":
                price_now,

            "price_then":
                price_then,

            "momentum_pct":
                momentum_pct,

            "volume_ratio":
                volume_ratio,

            "direction":
                direction

        }

    except Exception as e:

        print(
            f"Momentum error: {e}"
        )

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

    # =============================================
    # MOMENTUM FILTER
    # =============================================

    if momentum_pct < MIN_MOMENTUM_PCT:

        return (
            None,
            "weak momentum",
            0,
            0
        )

    # =============================================
    # VOLUME FILTER
    # =============================================

    if (
        momentum["volume_ratio"]
        < MIN_VOLUME_RATIO
    ):

        return (
            None,
            "low volume",
            0,
            0
        )

    yes_price = market["yes_price"]

    # =============================================
    # FAIR VALUE MODEL
    # =============================================

    if momentum["direction"] == "up":

        signal = "BUY_YES"

        expected_yes_price = (
            0.50
            + (
                momentum_pct
                * MOMENTUM_FACTOR
            )
        )

        divergence = (
            expected_yes_price
            - yes_price
        )

    else:

        signal = "BUY_NO"

        expected_yes_price = (
            0.50
            - (
                momentum_pct
                * MOMENTUM_FACTOR
            )
        )

        divergence = (
            yes_price
            - expected_yes_price
        )

    # =============================================
    # EDGE FILTER
    # =============================================

    if divergence < MIN_DIVERGENCE_EDGE:

        return (
            None,
            "no edge",
            expected_yes_price,
            divergence
        )

    return (
        signal,
        "VALID",
        expected_yes_price,
        divergence
    )

# =====================================================
# LOG MARKET
# =====================================================

def log_market(
    market,
    momentum,
    expected_yes_price,
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

            datetime.utcnow()
            .isoformat(),

            market["slug"],

            momentum["price_now"],

            momentum["price_then"],

            momentum["momentum_pct"],

            momentum["volume_ratio"],

            expected_yes_price,

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
    expected_yes_price,
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

            datetime.utcnow()
            .isoformat(),

            market["slug"],

            signal,

            momentum["price_now"],

            momentum["momentum_pct"],

            momentum["volume_ratio"],

            expected_yes_price,

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

            # =====================================
            # FETCH PM MARKET
            # =====================================

            market = fetch_market()

            if not market:

                print(
                    "Market fetch failed"
                )

                time.sleep(5)

                continue

            # =====================================
            # FETCH BTC MOMENTUM
            # =====================================

            momentum = (
                get_binance_momentum()
            )

            if not momentum:

                print(
                    "Momentum fetch failed"
                )

                time.sleep(5)

                continue

            time_left = (
                get_time_left()
            )

            (
                signal,
                status,
                expected_yes_price,
                divergence
            ) = analyze_signal(
                momentum,
                market
            )

            # =====================================
            # PRINT LIVE STATUS
            # =====================================

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
                f"Expected YES: "
                f"{expected_yes_price:.3f}"
            )

            print(
                f"Actual YES: "
                f"{market['yes_price']:.3f}"
            )

            print(
                f"NO Price: "
                f"{market['no_price']:.3f}"
            )

            print(
                f"Divergence: "
                f"{divergence:.3f}"
            )

            print(
                f"Time Left: "
                f"{time_left}s"
            )

            # =====================================
            # LOG ALL MARKET DATA
            # =====================================

            log_market(
                market,
                momentum,
                expected_yes_price,
                divergence,
                time_left
            )

            # =====================================
            # FINAL SIGNAL WINDOW
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
                    expected_yes_price,
                    divergence,
                    time_left
                )

            else:

                print(
                    f"Skip: {status}"
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
                f"Main loop error: {e}"
            )

            time.sleep(5)

# =====================================================
# START
# =====================================================

if __name__ == "__main__":

    main()
