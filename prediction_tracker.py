import sqlite3
from datetime import datetime

# ============================================================
# DATABASE
# ============================================================

DB_NAME = "btc_bot.db"

conn = sqlite3.connect(DB_NAME)

cursor = conn.cursor()

# ============================================================
# GET LAST CANDLE
# ============================================================

cursor.execute("""

SELECT
    candle_time,
    direction
FROM candles_5m
ORDER BY id DESC
LIMIT 1

""")

latest_candle = cursor.fetchone()

if latest_candle is None:

    print("No candles found.")

    exit()

latest_candle_time = latest_candle[0]

actual_result = latest_candle[1]

# ============================================================
# GET LATEST PREDICTION
# ============================================================

cursor.execute("""

SELECT
    id,
    prediction_time,
    candle_time,
    signal,
    confidence
FROM predictions

WHERE actual_result IS NULL

ORDER BY id ASC
LIMIT 1

""")

prediction = cursor.fetchone()

if prediction is None:

    print("No pending predictions.")

    exit()

prediction_id = prediction[0]

prediction_signal = prediction[3]

# ============================================================
# CHECK MATCHING CANDLE
# ============================================================

prediction_candle_time = prediction[2]

if prediction_candle_time != latest_candle_time:

    print("Waiting for matching candle close.")

    exit()

# ============================================================
# CALCULATE RESULT
# ============================================================

outcome = "LOSS"

if prediction_signal == actual_result:

    outcome = "WIN"

# ============================================================
# UPDATE PREDICTION
# ============================================================

cursor.execute("""

UPDATE predictions

SET
    actual_result = ?,
    outcome = ?

WHERE id = ?

""", (

    actual_result,
    outcome,
    prediction_id
))

conn.commit()

# ============================================================
# OUTPUT
# ============================================================

print("\n================================================")
print("PREDICTION RESULT UPDATED")
print("================================================")

print("CANDLE TIME :", latest_candle_time)

print("PREDICTION  :", prediction_signal)

print("ACTUAL      :", actual_result)

print("OUTCOME     :", outcome)
