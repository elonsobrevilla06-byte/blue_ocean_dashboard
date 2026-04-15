from db_connector import get_connection_mainland
from datetime import datetime



def get_cash_in_out(id=None):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        if id:
            cursor.execute(
                "SELECT * FROM cash_in_out WHERE id = %s",
                (id,)
            )
            return cursor.fetchone()

        cursor.execute("SELECT * FROM cash_in_out ORDER BY datetime DESC")
        return cursor.fetchall()

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()


def post_cash_in_out(data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        sql = """
        INSERT INTO cash_in_out (
            amount,
            type,
            datetime,
            notes,
            reference
        ) VALUES (%s, %s, %s,%s, %s)
        """

        values = (
            data.get("amount"),
            data.get("type"),
            data.get("datetime") or datetime.now(),
            data.get("notes") or "N/A",
            data.get("reference") or "N/A"
        )

        cursor.execute(sql, values)
        conn.commit()

        return {
            "status": "success",
            "id": cursor.lastrowid
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()