from db_connector import get_connection_mainland, get_connection_floatingbar

def mainland_employee_login(employee_id, password):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM employee_management WHERE employee_id = %s AND password = %s",
        (employee_id, password)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def verify_employee_mainland(employee_id):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM employee_management WHERE employee_id = %s", (employee_id,)
    )

    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


# ===================================================
#               FLOATING BAR
# ===================================================

def floatingbar_employee_login(employee_id, password):
    conn = get_connection_floatingbar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM employee_management WHERE employee_id = %s AND password = %s",
        (employee_id, password)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def verify_employee_floatingbar(employee_id):
    conn = get_connection_floatingbar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM employee_management WHERE employee_id = %s", (employee_id,)
    )

    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result
