from db_connector import get_connection_mainland
from datetime import datetime


def get_register(id = None):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        if id:
            cursor.execute(
                "SELECT * FROM register WHERE id = %s",
                (id,)
            )
            row = cursor.fetchone()
            return row
        else:
            cursor.execute(
                "SELECT * FROM register" 
            )
            result = cursor.fetchall()
            return result
        
    except Exception as e:
        return {"status" : "error", "message" : str(e)}
    
    finally:
        cursor.close()
        conn.close()

def post_register(register_data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        sql_query = """
        INSERT INTO register (
            drawer_id,
            register_name,
            location,
            notes
        ) VALUES (%s, %s, %s, %s)
        """

        values = [
            register_data.get("drawer_id"),
            register_data.get("register_name"),
            register_data.get("location"),
            register_data.get("notes")
        ]

        cursor.execute(sql_query, values)
        conn.commit()

        return {
            "status": "success",
            "register_id": cursor.lastrowid
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def put_register_by_id(register_id, register_data):
    conn = None
    cursor = None

    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        # Check if exists
        cursor.execute(
            "SELECT * FROM register WHERE id = %s",
            (register_id,)
        )
        row = cursor.fetchone()

        if not row:
            return {"status": "error", "message": "Register not found"}

        drawer_id = register_data.get("drawer_id") or row["drawer_id"]
        register_name = register_data.get("register_name") or row["register_name"]
        location = register_data.get("location") or row["location"]
        notes = register_data.get("notes") or row["notes"]

        sql = """
        UPDATE register SET
            drawer_id=%s,
            register_name=%s,
            location=%s,
            notes=%s
        WHERE id=%s
        """

        values = [
            drawer_id,
            register_name,
            location,
            notes,
            register_id
        ]

        cursor.execute(sql, values)
        conn.commit()

        return {
            "status": "success",
            "message": "Register updated"
        }

    except Exception as e:
        if conn:
            conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_register_by_id(register_id):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM register WHERE id = %s",
            (register_id,)
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
