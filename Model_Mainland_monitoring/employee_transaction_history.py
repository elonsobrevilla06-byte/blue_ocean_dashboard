from db_connector import get_connection_mainland

def get_employee_transaction(employee_id = None):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        if employee_id:
            cursor.execute("SELECT * FROM employee_transaction_history WHERE employee_id = %s", (employee_id,))
            row = cursor.fetchall()

            return row
        else:
            cursor.execute("SELECT * FROM employee_transaction_history")
            result = cursor.fetchall()

            return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()



def post_employee_transaction(employee_data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        sql_query = """
        INSERT INTO employee_transaction_history (
            employee_id, firstName, lastName, position,
             department, starting_cash, cash_variance
        ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        values = [
            employee_data.get("employee_id"),
            employee_data.get("firstName"), 
            employee_data.get("lastName"),
            employee_data.get("position"), 
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

