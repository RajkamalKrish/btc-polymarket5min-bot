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

FEE_RATE = 0.10

SIGNALS_CSV = "signals.csv"
MARKET_CSV = "market_data.csv"
RESOLVED_CSV = "resolved_signals.csv"

# =====================================================
# OPEN SIGNAL TRACKER
# =====================================================

open_signals = []

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
                "pm_price_to_beat",
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
                "pm_price_to_beat",
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
# RESOLVED CSV
# =====================================================

def setup_resolved_csv():

    try:

        with open(
            RESOLVED_CSV,
            "x",
            newline=""
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "timestamp",
                "market_slug",
                "signal",
                "entry_price",
                "start_price",
                "end_price",
                "winner",
                "result",
                "pnl",
                "divergence",
                "momentum_pct"
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
# EXTRACT PM PRICE
# =====================================================

def extract_price_to_beat(market):

    possible_fields = [

        "priceToBeat",
        "strikePrice",
        "referencePrice",
        "btcPrice",
        "initialPrice"

    ]

    for field in possible_fields:

        if field in market:

            try:

                return float(
                    market[field]
                )

            except Exception:

                pass

    # =============================================
    # DEBUG FULL JSON
    # =============================================

    print()
    print("=" * 60)
    print("FULL MARKET JSON")
    print("=" * 60)

    try:

        print(
            json.dumps(
                market,
                indent=2
            )[:5000]
        )

    except Exception:
        pass

    print("=" * 60)

    return None

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

        price_to_beat = (
            extract_price_to_beat(
                market
            )
        )

        return {

            "slug":
                slug,

            "yes_price":
                yes_price,

            "no_price":
                no_price,

            "price_to_beat":
                price_to_beat

        }

    except Exception as e:

        print(
            f"Fetch error: {e}"
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

        return None, "weak momentum", 0

    if (
        momentum["volume_ratio"]
        < MIN_VOLUME_RATIO
    ):

        return None, "low volume", 0

    yes_price = market["yes_price"]

    # =============================================
    # FAIR VALUE
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
            divergence
        )

    return (
        signal,
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

            market["price_to_beat"],

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

            market["price_to_beat"],

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

    global open_signals

    setup_csv()

    setup_resolved_csv()

    print("=" * 60)

    print(
        "BTC PM-NATIVE "
        "SELF-RESOLVING BOT"
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

            (
                signal,
                result,
                divergence
            ) = analyze_signal(
                momentum,
                market
            )

            expected_yes_price = (
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
                f"PM Price To Beat: "
                f"{market['price_to_beat']}"
            )

            print(
                f"BTC Now: "
                f"${momentum['price_now']:,.2f}"
            )

            print(
                f"Momentum: "
                f"{momentum['momentum_pct']:+.3f}%"
            )

            print(
                f"YES Price: "
                f"{market['yes_price']:.3f}"
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
            # LOG MARKET
            # =====================================

            log_market(
                market,
                momentum,
                expected_yes_price,
                divergence,
                time_left
            )

            # =====================================
            # SIGNAL
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

                entry_price = (
                    market["yes_price"]
                    if signal == "BUY_YES"
                    else market["no_price"]
                )

                open_signals.append({

                    "market_slug":
                        market["slug"],

                    "signal":
                        signal,

                    "entry_price":
                        entry_price,

                    "start_price":
                        market[
                            "price_to_beat"
                        ],

                    "divergence":
                        divergence,

                    "momentum_pct":
                        momentum[
                            "momentum_pct"
                        ]

                })

            else:

                print(
                    f"Skip: {result}"
                )

            # =====================================
            # RESOLVE USING NEXT PM EVENT
            # =====================================

            remaining_signals = []

            current_market_slug = (
                get_market_slug()
            )

            current_market = (
                fetch_market()
            )

            for s in open_signals:

                current_slug = (
                    s["market_slug"]
                )

                current_ts = int(
                    current_slug
                    .split("-")[-1]
                )

                next_ts = (
                    current_ts + 300
                )

                next_slug = (
                    f"btc-updown-5m-{next_ts}"
                )

                # =================================
                # WAIT FOR NEXT MARKET
                # =================================

                if (
                    current_market_slug
                    != next_slug
                ):

                    remaining_signals.append(
                        s
                    )

                    continue

                try:

                    if not current_market:

                        remaining_signals.append(
                            s
                        )

                        continue

                    end_price = (
                        current_market[
                            "price_to_beat"
                        ]
                    )

                    if (
                        end_price is None
                        or
                        s["start_price"]
                        is None
                    ):

                        remaining_signals.append(
                            s
                        )

                        continue

                    # =================================
                    # TRUE PM-NATIVE RESOLUTION
                    # =================================

                    winner = (
                        "YES"
                        if end_price
                        >= s["start_price"]
                        else "NO"
                    )

                    # =================================
                    # WIN / LOSS
                    # =================================

                    if (
                        s["signal"]
                        == "BUY_YES"
                    ):

                        won = (
                            winner == "YES"
                        )

                    else:

                        won = (
                            winner == "NO"
                        )

                    if won:

                        pnl = (
                            (
                                1
                                - s["entry_price"]
                            )
                            * (
                                1 - FEE_RATE
                            )
                        )

                        result = "WIN"

                    else:

                        pnl = (
                            -s["entry_price"]
                        )

                        result = "LOSS"

                    print()

                    print("=" * 60)

                    print(
                        f"RESOLVED: "
                        f"{s['signal']} "
                        f"→ {result}"
                    )

                    print(
                        f"Start Price: "
                        f"{s['start_price']}"
                    )

                    print(
                        f"End Price: "
                        f"{end_price}"
                    )

                    print(
                        f"Winner: "
                        f"{winner}"
                    )

                    print(
                        f"PnL: "
                        f"{pnl:.4f}"
                    )

                    print("=" * 60)

                    # =================================
                    # SAVE
                    # =================================

                    with open(
                        RESOLVED_CSV,
                        "a",
                        newline=""
                    ) as f:

                        writer = csv.writer(f)

                        writer.writerow([

                            datetime.utcnow()
                            .isoformat(),

                            s["market_slug"],

                            s["signal"],

                            s["entry_price"],

                            s["start_price"],

                            end_price,

                            winner,

                            result,

                            round(
                                pnl,
                                4
                            ),

                            s["divergence"],

                            s["momentum_pct"]

                        ])

                except Exception as e:

                    print(
                        f"Resolve error: {e}"
                    )

            open_signals = (
                remaining_signals
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
