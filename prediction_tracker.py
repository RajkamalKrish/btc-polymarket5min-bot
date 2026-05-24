# prediction_tracker.py

import sqlite3
import time

# ============================================================
# DATABASE
# ============================================================

DB_NAME = "btc_bot.db"

conn = sqlite3.connect(
    DB_NAME,
    check_same_thread=False
)

cursor = conn.cursor()

# ============================================================
# START
# ============================================================

print("\n================================================")
print("BTC PREDICTION TRACKER")
print("================================================")

# ============================================================
# MAIN LOOP
# ============================================================

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

        ORDER BY id ASC

        """)

        predictions = cursor.fetchall()

        # ====================================================
        # NO PENDING PREDICTIONS
        # ====================================================

        if not predictions:

            print(
                "Tracker running... "
                "No pending predictions."
            )

            time.sleep(15)

            continue

        updated = False

        # ====================================================
        # PROCESS PREDICTIONS
        # ====================================================

        for prediction in predictions:

            prediction_id = prediction[0]

            prediction_signal = prediction[1]

            prediction_candle_time = prediction[2]

            # ================================================
            # WAIT FOR TARGET CANDLE TO CLOSE
            # ================================================

            if prediction_candle_time != latest_candle_time:

                print(
                    f"Waiting for candle close: "
                    f"{prediction_candle_time}"
                )

                continue

            # ================================================
            # CALCULATE RESULT
            # ================================================

            outcome = "LOSS"

            if prediction_signal == actual_result:

                outcome = "WIN"

            # ================================================
            # UPDATE DATABASE
            # ================================================

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

            # ================================================
            # OUTPUT
            # ================================================

            print("\n================================================")
            print("PREDICTION UPDATED")
            print("================================================")

            print("CANDLE TIME :", latest_candle_time)

            print("PREDICTION  :", prediction_signal)

            print("ACTUAL      :", actual_result)

            print("OUTCOME     :", outcome)

        # ====================================================
        # NO UPDATES
        # ====================================================

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
