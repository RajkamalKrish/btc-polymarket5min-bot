import pandas as pd

# ============================================================
# RSI
# ============================================================

def calculate_rsi(df, period=14):

    delta = df['close'].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# ============================================================
# ATR
# ============================================================

def calculate_atr(df, period=14):

    high_low = df['high'] - df['low']

    high_close = (df['high'] - df['close'].shift()).abs()

    low_close = (df['low'] - df['close'].shift()).abs()

    tr = pd.concat([
        high_low,
        high_close,
        low_close
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    return atr

# ============================================================
# EMA
# ============================================================

def calculate_ema(df, period=9):

    return df['close'].ewm(
        span=period,
        adjust=False
    ).mean()
