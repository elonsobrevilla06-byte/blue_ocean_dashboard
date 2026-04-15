from db_connector import get_connection_mainland


def get_mainland_table(table_id=None):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    try:
        if table_id:
            cursor.execute(
                "SELECT * FROM table_management WHERE table_id = %s",
                (table_id,)
            )
            result = cursor.fetchone()
        else:
            cursor.execute("SELECT * FROM table_management")
            result = cursor.fetchall()

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()