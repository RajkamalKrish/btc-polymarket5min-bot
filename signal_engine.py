import sqlite3
    SELECT *
    FROM candles_5m
    ORDER BY id ASC
    ''',
    conn
)

# ============================================================
# INDICATORS
# ============================================================

df['rsi'] = calculate_rsi(df)

df['atr'] = calculate_atr(df)

df['ema9'] = calculate_ema(df, 9)

df['ema21'] = calculate_ema(df, 21)

# ============================================================
# LATEST CANDLE
# ============================================================

latest = df.iloc[-1]

signal = 'SKIP'

confidence = 0.50

# ============================================================
# SIGNAL LOGIC
# ============================================================

# bullish
if (
    latest['close'] > latest['ema9']
    and latest['ema9'] > latest['ema21']
    and latest['rsi'] > 55
    and latest['atr'] > 20
):

    signal = 'UP'
    confidence = 0.62

# bearish
elif (
    latest['close'] < latest['ema9']
    and latest['ema9'] < latest['ema21']
    and latest['rsi'] < 45
    and latest['atr'] > 20
):

    signal = 'DOWN'
    confidence = 0.62

# ============================================================
# OUTPUT
# ============================================================

print('\n================================================')
print('BTC SIGNAL ENGINE')
print('================================================')

print('TIME       :', latest['candle_time'])
print('CLOSE      :', round(latest['close'], 2))
print('RSI        :', round(latest['rsi'], 2))
print('ATR        :', round(latest['atr'], 2))
print('EMA9       :', round(latest['ema9'], 2))
print('EMA21      :', round(latest['ema21'], 2))
print('SIGNAL     :', signal)
print('CONFIDENCE :', confidence)
