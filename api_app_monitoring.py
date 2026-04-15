from Model_Mainland_monitoring.mainland_transaction_model import get_mainland_transaction
from Model_Mainland_monitoring.mainland_employee_management_model import get_mainland_employee, put_mainland_employee_by_id, get_mainland_employee_by_emp_id, post_mainland_employee, delete_mainland_employee
from Model_Mainland_monitoring.mainland_table_management_model import get_mainland_table
from Model_Mainland_monitoring.employee_transaction_history import get_employee_transaction, post_employee_transaction
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# --------------------------------------------------------

#             API FOR SALES MONITORING

# --------------------------------------------------------


FLOATING_API_URL_EMPLOYEES = "http://10.104.120.221:5000/floatingbar/employees"
FLOATING_API_URL_TRANSACTION = "http://10.104.120.221:5000/floatingbar/transaction"
FLOATING_API_URL_TABLES = "http://10.104.120.221:5000/floatingbar/table_management"
FLOATING_API_URL_MENU = "http://10.104.120.221:5000/floatingbar/menu"
# --------------------------------------------------------

#               TRANSACTIONS/MONITORING

# --------------------------------------------------------

@app.route("/monitoring/mainland/transaction")
@app.route("/monitoring/mainland/transaction/<string:transaction_id>")
def get_mainland_transaction_route_monitoring(transaction_id=None):
    try:
        result = get_mainland_transaction(transaction_id=transaction_id)

        if transaction_id and not result:
            return jsonify({"status": "error","message": "Transaction not found"}), 404
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
@app.route("/monitoring/transaction/floatingbar")
@app.route("/monitoring/transaction/floatingbar/<string:transaction_id>")
def get_floating_transaction_route_monitoring(transaction_id = None):
    try:
        if transaction_id is None:
            url = FLOATING_API_URL_TRANSACTION
        else:
            url = f"{FLOATING_API_URL_TRANSACTION}/{transaction_id}"
        
        response = requests.get(url)

        return jsonify({"status": "success", "data" : response.json()})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}),500
    
@app.route("/monitoring/all/transactions")
@app.route("/monitoring/all/transactions/<string:transaction_id>")
def get_all_transactions(transaction_id=None):
    print("ROUTE HIT")
    try:
        mainland_data = get_mainland_transaction(transaction_id=transaction_id)

        if transaction_id:
            floating_url = f"{FLOATING_API_URL_TRANSACTION}/{transaction_id}"
        else:
            floating_url = FLOATING_API_URL_TRANSACTION
            
        try:
            floating_response = requests.get(floating_url, timeout=5)
            floating_data = floating_response.json()
        except Exception as e:
            floating_data = {"status": "error", "message": "Floating unavailable"}
       
       
        print(f"Mainland: {mainland_data}")
        print(f"Floating: {floating_data}")
      
        return jsonify({
            "status": "success",
            "mainland": mainland_data,
            "floating": floating_data
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
# --------------------------------------------------------

#                   TABLES/MONITORING

# --------------------------------------------------------
@app.route("/monitoring/mainland/table_management")
@app.route("/monitoring/mainland/table_management/<int:table_id>", methods=["GET"])
def get_table_route_monitoring(table_id=None):
    try:
        result = get_mainland_table(table_id=table_id)

        if table_id and not result:
            return jsonify({"status": "error","message": "Table not found" }), 404

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/monitoring/table_management/floatingbar")
@app.route("/monitoring/table_management/floatingbar/<int:table_id>")
def get_floating_table_route_monitoring(table_id = None):
    try:
        if table_id is None:
            url = FLOATING_API_URL_TABLES
        else:
            url = f"{FLOATING_API_URL_TABLES}/{table_id}"

        response = requests.get(url)

        return jsonify({"status":"sucess", "data": response.json()})
    

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    

# --------------------------------------------------------

#                   EMPLOYEES/MONITORING

# --------------------------------------------------------

#FOR FETCHING ONLY MAINLAND
@app.route("/monitoring/mainland/employees")
@app.route("/monitoring/mainland/employees/<int:id>")
def get_employee_route_monitoring(id=None):
    try:
        result = get_mainland_employee(id=id)
        if id and not result:
            return jsonify({"status": "error","message": "Employee not found"}), 404

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/monitoring/employees/floatingbar")    
@app.route("/monitoring/employees/floatingbar/<int:id>")
def get_floating_employee_route_monitoring(id=None):
    try:
        if id is None:
            url = FLOATING_API_URL_EMPLOYEES  
        else:
            url = f"{FLOATING_API_URL_EMPLOYEES}/{id}"

        response = requests.get(url)

        return jsonify({
            "status": "success",
            "data": response.json()
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@app.route("/monitoring/employees/floatingbar")    
@app.route("/monitoring/employees/floatingbar/<int:id>")
def get_all_employees(id = None):
    try:
        mainland_data = get_mainland_employee(id=id)

        if id:
            floating_url = f"{FLOATING_API_URL_EMPLOYEES}/{id}"
        else:
            floating_url = FLOATING_API_URL_EMPLOYEES

        try:
            floating_response = requests.get(floating_url, timeout=5)
            floating_data = floating_response.json()

        except Exception as e:
            floating_data = {"status": "error", "message": str(e)}
        return jsonify({
            "status": "success",
            "mainland": mainland_data,
            "floating": floating_data

        }), 200
    except Exception as e:
        return jsonify({"status" : "error", "message": str(e)})
    
@app.route("/monitoring/employees/floatingbar", methods = ["POST"])
def post_employee_floatingbar_monitoring():
    try:
        data = request.get_json()
        response = requests.post(f"{FLOATING_API_URL_EMPLOYEES}", json = data, timeout= 5)
        post_mainland_employee(data)
        return jsonify({"status": "success", "data": response.json()})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
#Update only the mainland
@app.route("/monitoring/employees/mainland/<string:employee_id>", methods=["PUT"])
def put_mainland_employee_route(employee_id):
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No input data provided"
            }), 400

        result = put_mainland_employee_by_id(employee_id, data)

        return jsonify({
            "status": "success",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
#Only updates for mainland to floatingbar
@app.route("/monitoring/employees/floatingbar/<string:employee_id>", methods = ["PUT"])
def put_employee_floatingbar_monitoring(employee_id):
    try:
        data = request.get_json()

        response = requests.put(f"{FLOATING_API_URL_EMPLOYEES}/{employee_id}", json = data)

        return jsonify({"status": "success", "floating_response" : response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

#Updates both mainland and floatingbar if kung mag decide kami na parehas nalang yung db
@app.route("/monitoring/employees/floatingbar/sync/<string:employee_id>", methods=["PUT"])
def put_employee_floatingbar_monitoring_sync(employee_id):
    try:
        data = request.get_json()
        floating_response = requests.put(
            f"{FLOATING_API_URL_EMPLOYEES}/{employee_id}",
            json=data,
            timeout=5
        )
        mainland_result = put_mainland_employee_by_id(employee_id, data)

        existing_employee = get_mainland_employee_by_emp_id(employee_id)
        print(existing_employee)
        history_data = {
            "employee_id": employee_id,
            "firstName": data.get("firstName") if data.get("firstName") is not None else existing_employee["firstName"],
            "lastName": data.get("lastName") if data.get("lastName") is not None else existing_employee["lastName"],
            "position": data.get("position") if data.get("position") is not None else existing_employee["position"],
            "department": data.get("department") if data.get("department") is not None else existing_employee["department"],
            "starting_cash": data.get("starting_cash") if data.get("starting_cash") is not None else existing_employee["starting_cash"],
            "cash_variance": data.get("cash_variance") if data.get("cash_variance") is not None else existing_employee["cash_variance"],
        }

        post_employee_transaction(history_data)

        return jsonify({
            "status": "success",
            "floating_response": floating_response.json(),
            "mainland_response": mainland_result
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Floating server error: {str(e)}"
        }), 502

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@app.route("/monitoring/employees/floatingbar/<string:employee_id>", methods = ["DELETE"])
def delete_employee_floatingbar_monitoring(employee_id = None):
    try:

        response = requests.delete(f"{FLOATING_API_URL_EMPLOYEES}/{employee_id}", timeout= 5)
        delete_mainland_employee(employee_id=employee_id)
        return jsonify({"status": "success", "data": response.json()})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    

# --------------------------------------------------------

#                   EMPLOYEES TRANSACTION/MONITORING

# --------------------------------------------------------

@app.route("/monitoring/employee_transaction")
@app.route("/monitoring/employee_transaction/<string:employee_id>")
def get_employee_transaction_monitoring(employee_id = None):
    try:
        result = get_employee_transaction(employee_id=employee_id)

        if employee_id and not result:
            return jsonify({"status": "error", "message": "Emplyoee transaction not found"}),400 
        return jsonify(result), 200
    

    except Exception as e:
        return jsonify({"status": "error", "message" : str(e)})


# --------------------------------------------------------

#                   MENU/MONITORING

# --------------------------------------------------------
@app.route("/monitoring/menu/floatingbar")
@app.route("/monitoring/menu/floatingbar/<int:id>")
def get_menu_floatingbar_monitoring(id = None):
    try:
        if id is None:
            url = FLOATING_API_URL_MENU
        else:
            url = f"{FLOATING_API_URL_MENU}/{id}"

        response = requests.get(url)

        return jsonify({"status": "success", "data": response.json()})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
@app.route("/monitoring/menu/floatingbar", methods = ["POST"])
def post_menu_floatingbar_monitoring():
    try:
        data = request.get_json()
        response = requests.post(FLOATING_API_URL_MENU, json=data, timeout= 5)

        return jsonify({"status": "success", "data": response.json()})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
@app.route("/monitoring/menu/floatingbar/<int:id>", methods = ["PUT"])
def put_menu_floatingbar_monitoring(id = None):
    try:
        data = request.get_json()
        response = requests.put(f"{FLOATING_API_URL_MENU}/{id}", json=data, timeout= 5)

        return jsonify({"status": "success", "data": response.json()})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
@app.route("/monitoring/menu/floatingbar/<int:id>", methods = ["DELETE"])
def delete_menu_floatingbar_monitoring(id = None):
    try:

        response = requests.delete(f"{FLOATING_API_URL_MENU}/{id}", timeout= 5)

        return jsonify({"status": "success", "data": response.json()})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)