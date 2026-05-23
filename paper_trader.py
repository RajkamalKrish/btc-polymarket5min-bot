import sqlite3
candles = pd.read_sql(
    '''
    SELECT *
    FROM candles_5m
    ORDER BY id ASC
    ''',
    conn
)

wins = 0
losses = 0

# ============================================================
# SIMPLE STRATEGY TEST
# ============================================================

for i in range(25, len(candles) - 1):

    current = candles.iloc[i]

    next_candle = candles.iloc[i + 1]

    signal = None

    # bullish continuation
    if (
        current['close'] > current['open']
        and current['range_value'] > 25
    ):

        signal = 'UP'

    # bearish continuation
    elif (
        current['close'] < current['open']
        and current['range_value'] > 25
    ):

        signal = 'DOWN'

    if signal is None:
        continue

    actual = next_candle['direction']

    if signal == actual:
        wins += 1
    else:
        losses += 1

# ============================================================
# RESULTS
# ============================================================

total = wins + losses

if total > 0:
    win_rate = (wins / total) * 100
else:
    win_rate = 0

print('\n================================================')
print('PAPER TRADING RESULTS')
print('================================================')
print('TOTAL TRADES :', total)
print('WINS         :', wins)
print('LOSSES       :', losses)
print('WIN RATE     :', round(win_rate, 2), '%')
