from db_connector import get_connection_mainland

def get_employee_drawer_history ():
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM employee_drawer_history")
        result = cursor.fetchall()

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def get_active_employee_drawer_history():
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM employee_drawer_history WHERE status = 'Active'")
        result = cursor.fetchall()

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()

def post_employee_drawer_history(data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor()

        starting_cash = float(data.get("starting_cash") or 0)

        sql_query = """
        INSERT INTO employee_drawer_history (
            drawer_id,
            register,
            cashier,
            start_time,
            end_time,
            starting_cash,
            ending_balance,
            total_sales,
            cash_variance,
            current_balance,
            status,
            assigned_to
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = [
            data.get("drawer_id"),
            data.get("register"),
            data.get("cashier"),
            data.get("start_time"),
            None,
            starting_cash,
            0,
            0,
            0,
            starting_cash,   
            "Active",
            data.get("assigned_to")  
        ]

        cursor.execute(sql_query, values)
        conn.commit()

        return {"status": "success", "id": cursor.lastrowid}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cursor.close()
        conn.close()


def end_employee_drawer_history_shift(data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        sql_query = """
            UPDATE employee_drawer_history
            SET 
                status = %s,
                end_time = NOW()
            WHERE assigned_to = %s AND status = %s
        """

        values = [
            "Closed",
            data.get("assigned_to"),
            "Active"
        ]

        cursor.execute(sql_query, values)
        conn.commit()

        return {
            "status": "success",
            "updated": cursor.rowcount
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        cursor.close()
        conn.close()
def put_employee_drawer_history(id, data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        # ----------------------------
        # FETCH EXISTING ROW
        # ----------------------------
        cursor.execute("""
            SELECT * FROM employee_drawer_history
            WHERE id = %s
        """, (id,))
        existing_row = cursor.fetchone()

        if not existing_row:
            return {"status": "error", "message": "Record not found"}

        if (existing_row["status"] or "").lower() != "active":
            return {
                "status": "error",
                "message": "Only Active drawers can be updated"
            }

        # ----------------------------
        # VALUES
        # ----------------------------
        starting_cash = float(existing_row["starting_cash"] or 0)

        # SALES (accumulate)
        existing_sales = float(existing_row["total_sales"] or 0)
        incoming_sales = float(data.get("total_sales") or 0)
        total_sales = existing_sales + incoming_sales

        # STATUS
        status = data.get("status") if data.get("status") else existing_row["status"]

        # ----------------------------
        # 🔥 FIX: DO NOT RECOMPUTE BALANCE
        # ----------------------------
        current_balance = float(existing_row["current_balance"] or 0)

        # ----------------------------
        # ENDING BALANCE
        # ----------------------------
        ending_balance = data.get("ending_balance")

        if ending_balance is None:
            ending_balance = existing_row["ending_balance"]

        ending_balance = float(ending_balance or 0)

        # ----------------------------
        # CASH VARIANCE
        # ----------------------------
        cash_variance = None

        if status == "Closed":
            # if no ending balance provided, assume system balance
            if data.get("ending_balance") is None:
                ending_balance = current_balance

            cash_variance = ending_balance - current_balance

        # ----------------------------
        # END TIME AUTO SET
        # ----------------------------
        end_time_sql = ""
        if status == "Closed" and existing_row["status"] != "Closed":
            end_time_sql = ", end_time = NOW()"

        # ----------------------------
        # UPDATE QUERY
        # ----------------------------
        sql_query = f"""
        UPDATE employee_drawer_history
        SET
            total_sales = %s,
            ending_balance = %s,
            cash_variance = %s,
            current_balance = %s,
            status = %s
            {end_time_sql}
        WHERE id = %s AND status = %s
        """

        values = [
            total_sales,
            ending_balance,
            cash_variance,
            current_balance,
            status,
            id,
            "Active"
        ]

        cursor.execute(sql_query, values)
        conn.commit()

        return {
            "status": "success",
            "total_sales": total_sales,
            "current_balance": current_balance,
            "ending_balance": ending_balance,
            "cash_variance": cash_variance,
            "updated_rows": cursor.rowcount
        }

    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }

def transfer_drawer_cashier(id, new_cashier):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM employee_drawer_history
            WHERE id = %s
        """, (id,))
        row = cursor.fetchone()

        if not row:
            return {"status": "error", "message": "Drawer not found"}

        if (row["status"] or "").lower() != "active":
            return {"status": "error", "message": "Only active drawers can be transferred"}

        # Update cashier
        cursor.execute("""
            UPDATE employee_drawer_history
            SET cashier = %s
            WHERE id = %s AND status = 'Active'
        """, (new_cashier, id))

        conn.commit()

        return {
            "status": "success",
            "message": "Cashier transferred successfully",
            "updated_rows": cursor.rowcount
        }

    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    
def put_employee_drawer_cash_current_balance(data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        register = data.get("register")
        if not register:
            return {"status": "error", "message": "Register is required"}

        cursor.execute("""
            SELECT * FROM employee_drawer_history
            WHERE register = %s AND status = 'Active'
            LIMIT 1
        """, (register,))

        existing_row = cursor.fetchone()

        if not existing_row:
            return {
                "status": "error",
                "message": "No active drawer found for this register"
            }

        # ----------------------------
        # OLD VALUES
        # ----------------------------
        old_current_balance = float(existing_row["current_balance"] or 0)
        total_sales = float(existing_row["total_sales"] or 0)

        # ----------------------------
        # CASH FLOW INPUT
        # ----------------------------
        cash_flow = float(data.get("current_balance") or 0)
        # + = cash in, - = cash out

        # ----------------------------
        # NEW BALANCE
        # ----------------------------
        new_current_balance = old_current_balance + cash_flow

        # ----------------------------
        # UPDATE ONLY ACTIVE + REGISTER
        # ----------------------------
        cursor.execute("""
            UPDATE employee_drawer_history
            SET current_balance = %s
            WHERE register = %s AND status = 'Active'
        """, (
            new_current_balance,
            register
        ))

        conn.commit()

        return {
            "status": "success",
            "register": register,
            "cash_flow": cash_flow,
            "previous_balance": old_current_balance,
            "new_current_balance": new_current_balance,
            "updated_rows": cursor.rowcount
        }

    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    
def put_employee_drawer_safe_register(data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        register = data.get("register")
        if not register:
            return {"status": "error", "message": "Register is required"}

        cursor.execute("""
            SELECT safe_deposit
            FROM employee_drawer_history
            WHERE register = %s AND status = 'Active'
            LIMIT 1
        """, (register,))

        existing_row = cursor.fetchone()

        if not existing_row:
            return {
                "status": "error",
                "message": "No active drawer found for this register"
            }


        old_safe = float(existing_row["safe_deposit"] or 0)


        add_safe = float(data.get("safe_deposit") or 0)

        if add_safe <= 0:
            return {
                "status": "error",
                "message": "Safe deposit must be greater than 0"
            }


        new_safe = old_safe + add_safe

        cursor.execute("""
            UPDATE employee_drawer_history
            SET safe_deposit = %s
            WHERE register = %s AND status = 'Active'
        """, (
            new_safe,
            register
        ))

        conn.commit()

        return {
            "status": "success",
            "register": register,
            "added_safe_deposit": add_safe,
            "previous_safe_deposit": old_safe,
            "new_safe_deposit": new_safe
        }

    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }



def put_employee_drawer_reconcile(data):
    try:
        conn = get_connection_mainland()
        cursor = conn.cursor(dictionary=True)

        register = data.get("register")
        if not register:
            return {"status": "error", "message": "Register is required"}

        # ----------------------------
        # GET ACTIVE DRAWER
        # ----------------------------
        cursor.execute("""
            SELECT id, current_balance, ending_balance
            FROM employee_drawer_history
            WHERE register = %s AND status = 'Active'
            LIMIT 1
        """, (register,))

        row = cursor.fetchone()

        if not row:
            return {
                "status": "error",
                "message": "No active drawer found for this register"
            }

        drawer_id = row["id"]
        current_balance = float(row["current_balance"] or 0)

        ending_balance = data.get("ending_balance")

      
        if ending_balance is None:
            ending_balance = current_balance

        ending_balance = float(ending_balance or 0)

        cash_variance = ending_balance - current_balance

        # ----------------------------
        # UPDATE + AUTO CLOSE
        # ----------------------------
        cursor.execute("""
            UPDATE employee_drawer_history
            SET 
                ending_balance = %s,
                cash_variance = %s,
                status = 'Closed',
                end_time = NOW()
            WHERE id = %s AND status = 'Active'
        """, (
            ending_balance,
            cash_variance,
            drawer_id
        ))

        conn.commit()

        return {
            "status": "success",
            "register": register,
            "current_balance": current_balance,
            "ending_balance": ending_balance,
            "cash_variance": cash_variance,
            "message": "Drawer reconciled and closed successfully"
        }

    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }