import sqlite3
import time

# ============================================================
# DATABASE
# ============================================================

DB_NAME = "btc_bot.db"

conn = sqlite3.connect(DB_NAME)

cursor = conn.cursor()

# ============================================================
# MAIN LOOP
# ============================================================

print("\n================================================")
print("BTC PREDICTION TRACKER")
print("================================================")

while True:

    try:

        # ====================================================
        # GET LATEST CLOSED CANDLE
        # ====================================================

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

            time.sleep(10)

            continue

        latest_candle_time = latest_candle[0]

        actual_result = latest_candle[1]

        # ====================================================
        # FIND PENDING PREDICTIONS
        # ====================================================

        cursor.execute("""

        SELECT
            id,
            signal,
            candle_time
        FROM predictions

        WHERE actual_result IS NULL

        """)

        predictions = cursor.fetchall()

        updated = False

        for prediction in predictions:

            prediction_id = prediction[0]

            prediction_signal = prediction[1]

            prediction_candle_time = prediction[2]

            # ================================================
            # MATCH CANDLE
            # ================================================

            if prediction_candle_time == latest_candle_time:

                outcome = "LOSS"

                if prediction_signal == actual_result:

                    outcome = "WIN"

                # ============================================
                # UPDATE RESULT
                # ============================================

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

                updated = True

                print("\n================================================")
                print("PREDICTION UPDATED")
                print("================================================")

                print("CANDLE TIME :", latest_candle_time)

                print("PREDICTION  :", prediction_signal)

                print("ACTUAL      :", actual_result)

                print("OUTCOME     :", outcome)

        if not updated:

            print(
                "Tracker running... "
                "No completed predictions yet."
            )

        # ====================================================
        # WAIT
        # ====================================================

        time.sleep(15)

    except Exception as e:

        print("\nTRACKER ERROR:", e)

        time.sleep(10)
