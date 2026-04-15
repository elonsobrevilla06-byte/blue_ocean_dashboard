from db_connector import get_connection_mainland



def get_mainland_employee(id=None):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    try:
        if id:
            cursor.execute(
                "SELECT * FROM employee_management WHERE id = %s",
                (id,)
            )
            result = cursor.fetchone()
        else:
            cursor.execute("SELECT * FROM employee_management")

            result = cursor.fetchall()
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def get_mainland_employee_by_emp_id(employee_id):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM employee_management WHERE employee_id = %s",
            (employee_id,)
        )

        result = cursor.fetchone()  
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
            department,
            starting_cash,
            cash_variance
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
            employee_data.get("department"),
            employee_data.get("starting_cash"),
            employee_data.get("cash_variance")
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

def put_mainland_employee_by_id(employee_id, employee_data):
    mainland_conn = None
    mainland_cursor = None

    try:
        mainland_conn = get_connection_mainland()
        mainland_cursor = mainland_conn.cursor(dictionary=True)

        mainland_cursor.execute(
            "SELECT * FROM employee_management WHERE employee_id = %s",
            (employee_id,)
        )
        row = mainland_cursor.fetchone()

        if not row:
            return {"status": "error", "message": "Employee not found in Mainland DB"}

        emp_id = employee_data.get("employee_id") or row["employee_id"]
        password = employee_data.get("password") or row["password"]
        firstName = employee_data.get("firstName") or row["firstName"]
        lastName = employee_data.get("lastName") or row["lastName"]
        position = employee_data.get("position") or row["position"]
        contact_number = employee_data.get("contact_number") or row["contact_number"]
        email = employee_data.get("email") or row["email"]
        status = employee_data.get("status") or row["status"]
        department = employee_data.get("department") or row["department"]
        starting_cash = employee_data.get("starting_cash") if employee_data.get("starting_cash") is not None else row["starting_cash"]
        cash_variance = employee_data.get("cash_variance") if employee_data.get("cash_variance") is not None else row["cash_variance"]

        sql = """
        UPDATE employee_management SET
            employee_id=%s, password=%s, firstName=%s, lastName=%s,
            position=%s, contact_number=%s, email=%s, status=%s,
            department=%s, starting_cash=%s, cash_variance=%s
        WHERE employee_id=%s
        """

        values = [
            emp_id, password, firstName, lastName,
            position, contact_number, email, status,
            department, starting_cash, cash_variance, employee_id
        ]

        mainland_cursor.execute(sql, values)
        mainland_conn.commit()

        return {"status": "success", "message": "Mainland employee updated"}

    except Exception as e:
        if mainland_conn:
            mainland_conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        if mainland_cursor:
            mainland_cursor.close()
        if mainland_conn:
            mainland_conn.close()

def delete_mainland_employee(employee_id):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM employee_management WHERE employee_id = %s",
            (employee_id,)
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

