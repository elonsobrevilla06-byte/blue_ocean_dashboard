from db_connector import get_connection_mainland, get_connection_floatingbar

def get_mainland_employee(id=None):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    try:
        if id:
            cursor.execute(
                "SELECT * FROM employee_management WHERE id = %s",
                (id,)
            )
        else:
            cursor.execute("SELECT * FROM employee_management")

        result = cursor.fetchall()
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def post_mainland_employee(employee_data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        sql_query = """
        INSERT INTO employee_management (
            employee_id,
            password,
            firstName,
            lastName,
            position,
            contact_number,
            email,
            status,
            department
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = [
            employee_data.get("employee_id"),
            employee_data.get("password"),
            employee_data.get("firstName"),
            employee_data.get("lastName"),
            employee_data.get("position"),
            employee_data.get("contact_number"),
            employee_data.get("email"),
            employee_data.get("status") or "Active",
            employee_data.get("department")
        ]

        cursor.execute(sql_query, values)
        conn.commit()

        return {"status": "success", "employee_id": cursor.lastrowid}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def put_mainland_employee(id, employee_data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        sql_query = """
        UPDATE employee_management
        SET
            employee_id = %s,
            password = %s,
            firstName = %s,
            lastName = %s,
            position = %s,
            contact_number = %s,
            email = %s,
            status = %s,
            department = %s
        WHERE id = %s
        """

        values = [
            employee_data.get("employee_id"),
            employee_data.get("password"),
            employee_data.get("firstName"),
            employee_data.get("lastName"),
            employee_data.get("position"),
            employee_data.get("contact_number"),
            employee_data.get("email"),
            employee_data.get("status"),
            employee_data.get("department"),
            id
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

def put_mainland_employee_by_id(employee_id, employee_data):
    floating_conn = None
    mainland_conn = None

    try:
        # Connect to both DBs
        floating_conn = get_connection_floatingbar()
        floating_cursor = floating_conn.cursor(dictionary=True)

        mainland_conn = get_connection_mainland()
        mainland_cursor = mainland_conn.cursor(dictionary=True)

        updated_any = False  # Track if we updated any DB

        # --- Floating Bar DB ---
        floating_cursor.execute(
            "SELECT * FROM employee_management WHERE employee_id = %s",
            (employee_id,)
        )
        floating_row = floating_cursor.fetchone()

        if floating_row:
            emp_id = employee_data.get("employee_id") or floating_row["employee_id"]
            password = employee_data.get("password") or floating_row["password"]
            firstName = employee_data.get("firstName") or floating_row["firstName"]
            lastName = employee_data.get("lastName") or floating_row["lastName"]
            position = employee_data.get("position") or floating_row["position"]
            contact_number = employee_data.get("contact_number") or floating_row["contact_number"]
            email = employee_data.get("email") or floating_row["email"]
            status = employee_data.get("status") or floating_row["status"]
            department = employee_data.get("department") or floating_row["department"]

            sql = """
            UPDATE employee_management
            SET employee_id=%s, password=%s, firstName=%s, lastName=%s,
                position=%s, contact_number=%s, email=%s, status=%s, department=%s
            WHERE employee_id=%s
            """
            values = [emp_id, password, firstName, lastName, position,
                      contact_number, email, status, department, employee_id]

            floating_cursor.execute(sql, values)
            floating_conn.commit()
            updated_any = True

        # --- Mainland DB ---
        mainland_cursor.execute(
            "SELECT * FROM employee_management WHERE employee_id = %s",
            (employee_id,)
        )
        mainland_row = mainland_cursor.fetchone()

        if mainland_row:
            emp_id = employee_data.get("employee_id") or mainland_row["employee_id"]
            password = employee_data.get("password") or mainland_row["password"]
            firstName = employee_data.get("firstName") or mainland_row["firstName"]
            lastName = employee_data.get("lastName") or mainland_row["lastName"]
            position = employee_data.get("position") or mainland_row["position"]
            contact_number = employee_data.get("contact_number") or mainland_row["contact_number"]
            email = employee_data.get("email") or mainland_row["email"]
            status = employee_data.get("status") or mainland_row["status"]
            department = employee_data.get("department") or mainland_row["department"]

            sql = """
            UPDATE employee_management
            SET employee_id=%s, password=%s, firstName=%s, lastName=%s,
                position=%s, contact_number=%s, email=%s, status=%s, department=%s
            WHERE employee_id=%s
            """
            values = [emp_id, password, firstName, lastName, position,
                      contact_number, email, status, department, employee_id]

            mainland_cursor.execute(sql, values)
            mainland_conn.commit()
            updated_any = True

        if not updated_any:
            return {"status": "error", "message": "Employee not found in either DB"}

        return {"status": "success", "message": "Employee updated successfully"}

    except Exception as e:
        if floating_conn:
            floating_conn.rollback()
        if mainland_conn:
            mainland_conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        if floating_conn:
            floating_cursor.close()
            floating_conn.close()
        if mainland_conn:
            mainland_cursor.close()
            mainland_conn.close()

def delete_mainland_employee(id):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM employee_management WHERE id = %s",
            (id,)
        )

        conn.commit()
        return {
            "status": "Successfully Deleted",
            "deleted_rows": cursor.rowcount
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()
