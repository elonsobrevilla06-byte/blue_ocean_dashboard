from db_connector import get_connection_mainland
import json
from datetime import datetime
from zoneinfo import ZoneInfo 

def get_mainland_transaction(transaction_id=None):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    try:
        if transaction_id:
            cursor.execute(
                "SELECT * FROM mainland_transaction WHERE transaction_id = %s",
                (transaction_id,)
            )
            row = cursor.fetchone()

            if row:
                if row["main_guest_information"]:
                    row["main_guest_information"] = json.loads(row["main_guest_information"])
                if row["add_on_guest"]:
                    row["add_on_guest"] = json.loads(row["add_on_guest"])

            return row
        else:
            cursor.execute("SELECT * FROM mainland_transaction")
            result = cursor.fetchall()

            for row in result:
                if row["main_guest_information"]:
                    row["main_guest_information"] = json.loads(row["main_guest_information"])
                if row["add_on_guest"]:
                    row["add_on_guest"] = json.loads(row["add_on_guest"])

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def get_mainland_reservations(transaction_id=None):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    try:
        if transaction_id:
            cursor.execute(
                """
                SELECT * FROM mainland_transaction 
                WHERE transaction_id = %s 
                AND transaction_id LIKE 'RSV%%'
                AND type_of_transaction = 'reservation'
                """,
                (transaction_id,)
            )
            row = cursor.fetchone()

            if row:
                if row["main_guest_information"]:
                    row["main_guest_information"] = json.loads(row["main_guest_information"])
                if row["add_on_guest"]:
                    row["add_on_guest"] = json.loads(row["add_on_guest"])

            return row

        else:
            cursor.execute(
                """
                SELECT * FROM mainland_transaction
                WHERE transaction_id LIKE 'RSV%'
                AND type_of_transaction = 'reservation'
                """
            )
            result = cursor.fetchall()

            for row in result:
                if row["main_guest_information"]:
                    row["main_guest_information"] = json.loads(row["main_guest_information"])
                if row["add_on_guest"]:
                    row["add_on_guest"] = json.loads(row["add_on_guest"])

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def post_mainland_transaction(data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        type_of_transaction = data.get("type_of_transaction")

        if type_of_transaction == "reservation":
            reservation_datetime = data.get("reservation_datetime")
        else:
            reservation_datetime = None

        total_net_billing = float(data.get("total_net_billing") or 0.00)
        total_amount_paid = float(data.get("total_amount_paid") or 0.00)
        total_change = total_amount_paid - total_net_billing

        insert_query = """
        INSERT INTO mainland_transaction (
            type_of_transaction,
            main_guest_information,
            add_on_guest,
            total_net_billing,
            total_amount_paid,
            total_change,
            mode_of_payment,
            reference_number,
            status,
            reservation_datetime,
            created_at,
            notes,
            deck_assigned,
            table_assigned,
            access_type,
            assigned_card_number,
            attended_by
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        time_now = datetime.now(ZoneInfo("Asia/Manila"))
        values = [
            type_of_transaction,
            json.dumps(data.get("main_guest_information")),
            json.dumps(data.get("add_on_guest") or []),
            total_net_billing,
            total_amount_paid,
            total_change,
            data.get("mode_of_payment"),
            data.get("reference_number"),
            data.get("status") or "pending",
            reservation_datetime,
            time_now,
            data.get("notes") or "N/A",
            data.get("deck_assigned"),
            data.get("table_assigned"),
            data.get("access_type"),
            data.get("assigned_card_number"),
            data.get("attended_by") or "N/A"
        ]

        
        cursor.execute(insert_query, values)

        last_id = cursor.lastrowid

        if type_of_transaction == "reservation":
            transaction_id = f"RSV-{time_now.strftime('%y%m%d%H%M')}" # 10 digits shorter
        else:
            transaction_id = f"TXN-{time_now.strftime('%y%m%d%H%M')}"

        cursor.execute(
            "UPDATE mainland_transaction SET transaction_id = %s WHERE id = %s",
            (transaction_id, last_id)
        )

        conn.commit()
        cursor.close()
        conn.close()
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "total_change": total_change
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    


def put_mainland_transaction(transaction_id, data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM mainland_transaction WHERE transaction_id = %s",
            (transaction_id,)
        )
        existing_row = cursor.fetchone()

        if not existing_row:
            return {"status": "error", "message": "Transaction not found"}

        type_of_transaction = data.get("type_of_transaction") or existing_row["type_of_transaction"]

        if type_of_transaction == "reservation":
            reservation_datetime = data.get("reservation_datetime") or existing_row["reservation_datetime"]
        else:
            reservation_datetime = None

        sql_query = """
        UPDATE mainland_transaction
        SET
            type_of_transaction = %s,
            main_guest_information = %s,
            add_on_guest = %s,
            total_net_billing = %s,
            total_amount_paid = %s,
            total_change = %s,
            mode_of_payment = %s,
            reference_number = %s,
            status = %s,
            reservation_datetime = %s,
            notes = %s,
            deck_assigned = %s,
            table_assigned = %s,
            access_type = %s,
            assigned_card_number = %s,
            attended_by = %s
        WHERE transaction_id = %s
        """

        values = [
            type_of_transaction,
            json.dumps(data.get("main_guest_information")) if data.get("main_guest_information") else existing_row["main_guest_information"],
            json.dumps(data.get("add_on_guest")) if data.get("add_on_guest") else existing_row["add_on_guest"],
            data.get("total_net_billing") if data.get("total_net_billing") is not None else existing_row["total_net_billing"],
            data.get("total_amount_paid") if data.get("total_amount_paid") is not None else existing_row["total_amount_paid"],
            data.get("total_change") if data.get("total_change") is not None else existing_row["total_change"],
            data.get("mode_of_payment") or existing_row["mode_of_payment"],
            data.get("reference_number") or existing_row["reference_number"],
            data.get("status") or existing_row["status"],
            reservation_datetime,
            data.get("notes") or existing_row["notes"],
            data.get("deck_assigned") or existing_row["deck_assigned"],
            data.get("table_assigned") or existing_row["table_assigned"],
            data.get("access_type") or existing_row["access_type"],
            data.get("assigned_card_number") or existing_row["assigned_card_number"],  # ✅ NEW
            data.get("attended_by") or existing_row["attended_by"],
            transaction_id
        ]

        cursor.execute(sql_query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "updated_rows": cursor.rowcount
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

        
def put_mainland_transaction_by_transaction_id(transaction_id, data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        # Fetch existing transaction
        cursor.execute(
            "SELECT * FROM mainland_transaction WHERE transaction_id = %s",
            (transaction_id,)
        )
        existing_row = cursor.fetchone()

        if not existing_row:
            return {"status": "error", "message": "Transaction not found"}

        # Automatically change RSV- to TXN- if it starts with RSV-
        if transaction_id.startswith("RSV-"):
            new_transaction_id = transaction_id.replace("RSV-", "TXN-", 1)
        else:
            new_transaction_id = transaction_id

        type_of_transaction = data.get("type_of_transaction") or existing_row["type_of_transaction"]

        if type_of_transaction == "reservation":
            reservation_datetime = data.get("reservation_datetime") or existing_row["reservation_datetime"]
        else:
            reservation_datetime = None

        sql_query = """
        UPDATE mainland_transaction
        SET
            transaction_id = %s,
            type_of_transaction = %s,
            main_guest_information = %s,
            add_on_guest = %s,
            total_net_billing = %s,
            total_amount_paid = %s,
            total_change = %s,
            mode_of_payment = %s,
            reference_number = %s,
            status = %s,
            reservation_datetime = %s,
            notes = %s,
            deck_assigned = %s,
            table_assigned = %s,
            access_type = %s,
            assigned_card_number = %s,
            attended_by = %s
        WHERE transaction_id = %s
        """

        values = [
            new_transaction_id,
            type_of_transaction,
            json.dumps(data.get("main_guest_information")) if data.get("main_guest_information") else existing_row["main_guest_information"],
            json.dumps(data.get("add_on_guest")) if data.get("add_on_guest") else existing_row["add_on_guest"],
            data.get("total_net_billing") if data.get("total_net_billing") is not None else existing_row["total_net_billing"],
            data.get("total_amount_paid") if data.get("total_amount_paid") is not None else existing_row["total_amount_paid"],
            data.get("total_change") if data.get("total_change") is not None else existing_row["total_change"],
            data.get("mode_of_payment") or existing_row["mode_of_payment"],
            data.get("reference_number") or existing_row["reference_number"],
            data.get("status") or existing_row["status"],
            reservation_datetime,
            data.get("notes") or existing_row["notes"],
            data.get("deck_assigned") or existing_row["deck_assigned"],
            data.get("table_assigned") or existing_row["table_assigned"],
            data.get("access_type") or existing_row["access_type"],
            data.get("assigned_card_number") or existing_row["assigned_card_number"],
            data.get("attended_by") or existing_row["attended_by"],
            transaction_id  # old transaction_id for WHERE
        ]

        cursor.execute(sql_query, values)
        conn.commit()

        return {
            "status": "success",
            "updated_rows": cursor.rowcount,
            "new_transaction_id": new_transaction_id
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()


def delete_mainland_transaction(transaction_id):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM mainland_transaction WHERE transaction_id = %s",
            (transaction_id,)
        )
        conn.commit()

        return {
            "status": "success",
            "deleted_rows": cursor.rowcount
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def check_reservation(deck, table, reservation_date):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        if not deck or not table or not reservation_date:
            return None

        query = """
            SELECT *
            FROM mainland_transaction
            WHERE deck_assigned = %s
              AND table_assigned = %s
              AND DATE(reservation_datetime) = %s
              AND status != 'billout'
            
        """
        cursor.execute(query, (deck, table, reservation_date))
        reservation = cursor.fetchall()
        return reservation 

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    finally:
        cursor.close()
        conn.close()