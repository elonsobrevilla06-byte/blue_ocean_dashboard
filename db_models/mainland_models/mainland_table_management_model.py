from db_connector import get_connection_mainland, get_connection_floatingbar


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

def get_mainland_table_by_transactionid(transaction_id):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    try:
        if transaction_id:
            cursor.execute("SELECT * FROM table_management WHERE transaction_id = %s", (transaction_id,))

            result = cursor.fetchone()

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()      

def get_mainland_table_by_tablename(table_name):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    try:
        if table_name:
            cursor.execute("""
                SELECT * 
                FROM table_management 
                WHERE LOWER(table_name) = LOWER(%s)
            """, (table_name,))

            result = cursor.fetchone()
            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def update_mainland_table_by_name(table_name, update_data, location=None):
    conn = get_connection_mainland()
    cursor = conn.cursor()

    try:
        if not update_data:
            return {"status": "error", "message": "No data to update"}

        fields = []
        values = []

        for key, value in update_data.items():
            fields.append(f"{key} = %s")
            values.append(value)

        # Add table_name to values
        values.append(table_name)

        # Build WHERE clause
        where_clause = "LOWER(table_name) = LOWER(%s)"
        if location:
            where_clause += " AND LOWER(location) = LOWER(%s)"
            values.append(location)

        query = f"""
            UPDATE table_management
            SET {', '.join(fields)}
            WHERE {where_clause}
        """

        cursor.execute(query, tuple(values))
        conn.commit()

        return {
            "status": "success",
            "rows_updated": cursor.rowcount
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()



def post_mainland_table(table_data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        sql_query = """
        INSERT INTO table_management (
            table_name,
            capacity,
            location,
            status,
            transaction_id
        ) VALUES (%s, %s, %s, %s, %s)
        """

        values = [
            table_data.get("table_name"),
            table_data.get("capacity"),
            table_data.get("location"),
            table_data.get("status") or "Available",
            table_data.get("transaction_id") or None
        ]

        cursor.execute(sql_query, values)
        conn.commit()

        return {"status": "success", "table_id": cursor.lastrowid}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()



def put_mainland_table(table_id, table_data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        transaction_id = table_data.get("transaction_id")
        
        if not transaction_id:
            status = "available"
            transaction_id = None
        else:
            status = table_data.get("status") or "occupied"


        sql_query = """
        UPDATE table_management
        SET
            table_name = %s,
            capacity = %s,
            location = %s,
            status = %s,
            transaction_id = %s
        WHERE table_id = %s
        """

        values = [
            table_data.get("table_name"),
            table_data.get("capacity"),
            table_data.get("location"),
            status,
            table_data.get("transaction_id") or None,
            table_id
        ]

        cursor.execute(sql_query, values)
        conn.commit()

        return {"status": "success", "updated_rows": cursor.rowcount}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def put_mainland_table_management_sync_by_name(table_name, table_data):
    mainland_conn = None
    floating_conn = None

    try:
        # Connect to both databases
        mainland_conn = get_connection_mainland()
        mainland_cursor = mainland_conn.cursor(dictionary=True)

        floating_conn = get_connection_floatingbar()
        floating_cursor = floating_conn.cursor(dictionary=True)

        # Look up table by table_name in Mainland
        mainland_cursor.execute(
            "SELECT * FROM table_management WHERE table_name = %s",
            (table_name,)
        )
        mainland_row = mainland_cursor.fetchone()

        if not mainland_row:
            return {"status": "error", "message": f"Table '{table_name}' not found in Mainland DB"}

        # Use new values if provided, otherwise fallback to existing ones
        capacity = table_data.get("capacity", mainland_row["capacity"])
        location = table_data.get("location", mainland_row["location"])
        transaction_id = table_data.get("transaction_id", mainland_row.get("transaction_id"))
        status = table_data.get("status")
        if status is None:
            status = "occupied" if transaction_id else "available"

        # Update Floating Bar if table exists there
        floating_cursor.execute(
            "SELECT * FROM table_management WHERE table_name = %s",
            (table_name,)
        )
        floating_row = floating_cursor.fetchone()
        updated_any = False

        if floating_row:
            sql = """
            UPDATE table_management
            SET capacity=%s, location=%s, status=%s, transaction_id=%s
            WHERE table_name=%s
            """
            values = [capacity, location, status, transaction_id, table_name]
            floating_cursor.execute(sql, values)
            floating_conn.commit()
            updated_any = True

        # Update Mainland table
        sql = """
        UPDATE table_management
        SET capacity=%s, location=%s, status=%s, transaction_id=%s
        WHERE table_name=%s
        """
        values = [capacity, location, status, transaction_id, table_name]
        mainland_cursor.execute(sql, values)
        mainland_conn.commit()

        return {
            "status": "success",
            "message": "Table synced to Floating Bar" if updated_any else "Table updated in Mainland only"
        }

    except Exception as e:
        if mainland_conn:
            mainland_conn.rollback()
        if floating_conn:
            floating_conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        if mainland_conn:
            mainland_cursor.close()
            mainland_conn.close()
        if floating_conn:
            floating_cursor.close()
            floating_conn.close()


def put_mainland_table_management_sync(table_id, table_data):
    mainland_conn = None
    floating_conn = None

    try:
        mainland_conn = get_connection_mainland()
        mainland_cursor = mainland_conn.cursor(dictionary=True)

        floating_conn = get_connection_floatingbar()
        floating_cursor = floating_conn.cursor(dictionary=True)


        mainland_cursor.execute(
            "SELECT * FROM table_management WHERE table_id = %s",
            (table_id,)
        )
        mainland_row = mainland_cursor.fetchone()

        if not mainland_row:
            return {"status": "error", "message": "Table not found in Mainland DB"}

   
        table_name = table_data.get("table_name", mainland_row["table_name"])
        capacity = table_data.get("capacity", mainland_row["capacity"])
        location = table_data.get("location", mainland_row["location"])

        transaction_id = table_data.get("transaction_id")
        if transaction_id == "":
            transaction_id = None
        elif transaction_id is None:
            transaction_id = mainland_row.get("transaction_id")

        
        status = table_data.get("status")
        if status is None:
            status = "occupied" if transaction_id else "available"

        floating_cursor.execute(
            "SELECT * FROM table_management WHERE table_id = %s",
            (table_id,)
        )
        floating_row = floating_cursor.fetchone()

        if floating_row:
            sql = """
            UPDATE table_management
            SET table_name=%s, capacity=%s, location=%s, status=%s, transaction_id=%s
            WHERE table_id=%s
            """
            values = [table_name, capacity, location, status, transaction_id, table_id]
            floating_cursor.execute(sql, values)
            floating_conn.commit()
            updated_any = True
        else:
            updated_any = False

   
        sql = """
        UPDATE table_management
        SET table_name=%s, capacity=%s, location=%s, status=%s, transaction_id=%s
        WHERE table_id=%s
        """
        values = [table_name, capacity, location, status, transaction_id, table_id]
        mainland_cursor.execute(sql, values)
        mainland_conn.commit()

        return {
            "status": "success",
            "message": "Table synced to Floating Bar" if updated_any else "Table updated in Mainland only"
        }

    except Exception as e:
        if mainland_conn:
            mainland_conn.rollback()
        if floating_conn:
            floating_conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        if mainland_conn:
            mainland_cursor.close()
            mainland_conn.close()
        if floating_conn:
            floating_cursor.close()
            floating_conn.close()

def delete_mainland_table(table_id):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM table_management WHERE table_id = %s",
            (table_id,)
        )

        conn.commit()
        return {"status": "Successfully Deleted", "deleted_rows": cursor.rowcount}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def remove_mainland_table_transaction(transaction_id):
    mainland_conn = None
    floating_conn = None

    try:
       
        mainland_conn = get_connection_mainland()
        mainland_cursor = mainland_conn.cursor()

       
        floating_conn = get_connection_floatingbar()
        floating_cursor = floating_conn.cursor()

       
        sql_mainland = """
        UPDATE table_management
        SET transaction_id = NULL, status = 'available'
        WHERE transaction_id = %s
        """
        mainland_cursor.execute(sql_mainland, (transaction_id,))
        mainland_conn.commit()


        sql_floating = """
        UPDATE table_management
        SET transaction_id = NULL, status = 'available'
        WHERE transaction_id = %s
        """
        floating_cursor.execute(sql_floating, (transaction_id,))
        floating_conn.commit()

        return {
            "status": "success",
            "message": "Transaction removed. Table is now Available in both Mainland and Floating Bar."
        }

    except Exception as e:
        if mainland_conn:
            mainland_conn.rollback()
        if floating_conn:
            floating_conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        if mainland_conn:
            mainland_cursor.close()
            mainland_conn.close()
        if floating_conn:
            floating_cursor.close()
            floating_conn.close()