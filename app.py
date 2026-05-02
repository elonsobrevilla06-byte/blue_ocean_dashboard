from flask import Flask, request, render_template, jsonify, session,url_for,flash, redirect, send_file
import copy
from Model_Mainland_monitoring.mainland_transaction_model import get_mainland_transaction, get_transaction_reserved
from Model_Mainland_monitoring.mainland_employee_management_model import get_mainland_employee, get_mainland_employee_by_emp_id, post_mainland_employee, put_mainland_employee_by_id, delete_mainland_employee
from Model_Mainland_monitoring.mainland_drawer_history import get_employee_drawer_history, put_employee_drawer_history, post_employee_drawer_history, end_employee_drawer_history_shift, transfer_drawer_cashier, put_employee_drawer_cash_current_balance, put_employee_drawer_safe_register, get_active_employee_drawer_history, put_employee_drawer_reconcile
from Model_Mainland_monitoring.register_model import get_register, post_register, put_register_by_id, delete_register_by_id
from Model_Mainland_monitoring.cash_in_out import get_cash_in_out, post_cash_in_out

from db_models.mainland_models.loging_and_verfication_model import mainland_employee_login, verify_employee_mainland, floatingbar_employee_login, verify_employee_floatingbar

import requests
import json
from collections import defaultdict
from datetime import datetime, timedelta

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

from openpyxl import Workbook
from openpyxl.utils import get_column_letter



from openpyxl import Workbook
import time
import threading
import requests


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

import csv
from email.utils import parsedate_to_datetime
import os

from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)

app.secret_key = os.getenv("api_secret_key")

FLOATING_API_URL_EMPLOYEES = "http://floatingbar.bigboysautomation.com/floatingbar/employees"
FLOATING_API_URL_TRANSACTION = "http://floatingbar.bigboysautomation.com/floatingbar/transaction"
FLOATING_API_URL_TABLES = "http://floatingbar.bigboysautomation.com/floatingbar/table_management"
FLOATING_API_URL_MENU = "http://floatingbar.bigboysautomation.com/floatingbar/menu"


# -------------------


# Export Data



# ------------------

def safe_parse_date(value):

    if not value:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):


        try:
            return parsedate_to_datetime(value)
        except:
            pass

 
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except:
            pass

    return None


def build_dashboard_data():
    return {
        "locations": {
            "mainland": {
                "kpis": get_mainland_transaction_kpis_data(),
                "charts": {
                    "revenue_overview": get_mainland_revenue_data(),
                    "weekly_sales": get_mainland_weekly_data()
                }
            },
            "floatingbar": {
                "kpis": get_floatingbar_transaction_kpis_data(),
                "charts": {
                    "revenue_overview": get_floatingbar_revenue_data(),
                    "weekly_sales": get_floatingbar_weekly_data()
                }
            }
        },
        "shared": {
            "reservations": get_shared_reservation_data(),
            "sales": get_shared_menu_sales_data(),
            "staff": get_shared_employee_rank_data()
        }
    }

@app.route("/export")
def export_excel():
    data = get_cash_in_out()

    wb = Workbook()
    ws = wb.active
    ws.title = "Cash In Out"

    ws.append(["ID", "Amount", "Type", "Datetime", "Reference", "Notes"])

    from datetime import datetime

    current_month = datetime.now().strftime("%Y-%m")

    for row in data:
        row_month = row['datetime'].strftime("%Y-%m")

        if row_month == current_month:
            ws.append([
                row['id'],
                row['amount'],
                row['type'],
                row['datetime'],
                row['reference'],
                row['notes']
            ])

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter

        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 2

    file_path = "cash_in_out.xlsx"
    wb.save(file_path)

    return send_file(file_path, as_attachment=True)



@app.route("/balance-sheet-export")
def export_balance_sheet():

    floating = GLOBAL_DATA["floating_transactions"]
    mainland = GLOBAL_DATA["mainland_transactions"]
    drawers = get_employee_drawer_history()

    wb = Workbook()
    ws = wb.active
    ws.title = "Balance Sheet"

    current_month = datetime.now().strftime("%Y-%m")

    # =========================
    # CALCULATIONS
    # =========================
    total_sales = 0
    total_paid = 0
    closed_cash = 0
    active_liability = 0

    # TRANSACTIONS
    for tx in floating + mainland:

        created_at = tx.get("created_at")

        if created_at:
            if isinstance(created_at, str):
                created_at = parsedate_to_datetime(created_at)

            if created_at.strftime("%Y-%m") == current_month:
                total_sales += tx.get("total_net_billing", 0) or 0
                total_paid += tx.get("total_amount_paid", 0) or 0

    # DRAWERS
    for d in drawers:

        start_time = d.get("start_time")

        if start_time:
            if isinstance(start_time, str):
                try:
                    start_time = parsedate_to_datetime(start_time)
                except:
                    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

            if start_time.strftime("%Y-%m") == current_month:

                if d.get("status") == "Closed":
                    closed_cash += d.get("ending_balance", 0) or 0

                elif d.get("status") == "Active":
                    active_liability += d.get("current_balance", 0) or 0

    # =========================
    # ACCOUNTING LOGIC
    # =========================
    cash = total_paid + closed_cash
    accounts_receivable = total_sales - total_paid

    total_assets = cash + accounts_receivable
    total_liabilities = active_liability
    equity = total_assets - total_liabilities

    # =========================
    # WRITE EXCEL (FORMATTED)
    # =========================
    ws.append(["BALANCE SHEET"])
    ws.append(["Month", current_month])
    ws.append([])

    # ASSETS
    ws.append(["ASSETS", ""])
    ws.append(["Cash", cash])
    ws.append(["Accounts Receivable", accounts_receivable])
    ws.append(["TOTAL ASSETS", total_assets])
    ws.append([])

    # LIABILITIES
    ws.append(["LIABILITIES", ""])
    ws.append(["Active Drawer Liability", total_liabilities])
    ws.append(["TOTAL LIABILITIES", total_liabilities])
    ws.append([])

    # EQUITY
    ws.append(["EQUITY", ""])
    ws.append(["Owner's Equity", equity])
    ws.append(["TOTAL L + E", total_liabilities + equity])

    # =========================
    # STYLE (BOLD HEADERS)
    # =========================
    from openpyxl.styles import Font

    bold = Font(bold=True)

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        if row[0].value in ["ASSETS", "LIABILITIES", "EQUITY",
                            "TOTAL ASSETS", "TOTAL LIABILITIES", "TOTAL L + E"]:
            for cell in row:
                cell.font = bold

    # AUTO WIDTH
    from openpyxl.utils import get_column_letter

    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)

        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 3

    # =========================
    # SAVE
    # =========================
    file_path = "balance_sheet.xlsx"
    wb.save(file_path)

    return send_file(file_path, as_attachment=True)




@app.route("/income-statement-export")
def export_income_statement():

    floating = GLOBAL_DATA["floating_transactions"]
    mainland = GLOBAL_DATA["mainland_transactions"]

    wb = Workbook()
    ws = wb.active
    ws.title = "Income Statement"

    current_month = datetime.now().strftime("%Y-%m")

    # =========================
    # CALCULATIONS
    # =========================
    revenue = 0
    cash_collected = 0

    for tx in floating + mainland:

        created_at = safe_parse_date(tx.get("created_at"))

        if created_at and created_at.strftime("%Y-%m") == current_month:
            revenue += tx.get("total_net_billing", 0) or 0
            cash_collected += tx.get("total_amount_paid", 0) or 0


    expenses = 0

    # FUTURE IDEA:
    # expenses = get_total_expenses()

    net_profit = revenue - expenses

    # =========================
    # WRITE EXCEL (STRUCTURED)
    # =========================
    ws.append(["INCOME STATEMENT"])
    ws.append(["Month", current_month])
    ws.append([])

    # REVENUE SECTION
    ws.append(["REVENUE", ""])
    ws.append(["Total Sales", revenue])
    ws.append([])

    # EXPENSE SECTION
    ws.append(["EXPENSES", ""])
    ws.append(["Operating Expenses", expenses])
    ws.append([])

    # PROFIT
    ws.append(["NET PROFIT", net_profit])
    ws.append([])

    # EXTRA INFO (optional but useful)
    ws.append(["Cash Collected (for reference)", cash_collected])

    # =========================
    # STYLE (BOLD HEADERS)
    # =========================
    from openpyxl.styles import Font
    bold = Font(bold=True)

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        if row[0].value in ["REVENUE", "EXPENSES", "NET PROFIT"]:
            for cell in row:
                cell.font = bold

    # AUTO WIDTH
    from openpyxl.utils import get_column_letter

    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)

        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 3

    # =========================
    # SAVE
    # =========================
    file_path = "income_statement.xlsx"
    wb.save(file_path)

    return send_file(file_path, as_attachment=True)

@app.route("/export-dashboard-pdf")
def export_dashboard_pdf():


    data = {
        "locations": {
            "mainland": {
                "kpis": get_mainland_transaction_kpis_data(),
                "charts": {
                    "revenue_overview": get_mainland_revenue_data(),
                    "weekly_sales": get_mainland_weekly_data()
                }
            },
            "floatingbar": {
                "kpis": get_floatingbar_transaction_kpis_data(),
                "charts": {
                    "revenue_overview": get_floatingbar_revenue_data(),
                    "weekly_sales": get_floatingbar_weekly_data()
                }
            }
        },
        "shared": {
            "reservations": get_shared_reservation_data(),
            "sales": get_shared_menu_sales_data(),
            "staff": get_shared_employee_rank_data()
        }
    }

    # =========================
    # PDF SETUP
    # =========================
    file_path = "dashboard_report.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    # =========================
    # TITLE
    # =========================
    elements.append(Paragraph("Business Dashboard Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # =========================
    # MAINLAND
    # =========================
    elements.append(Paragraph("Mainland KPIs", styles["Heading2"]))
    for k, v in data["locations"]["mainland"]["kpis"].items():
        elements.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    # =========================
    # FLOATINGBAR
    # =========================
    elements.append(Paragraph("Floating Bar KPIs", styles["Heading2"]))
    for k, v in data["locations"]["floatingbar"]["kpis"].items():
        elements.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    # =========================
    # RESERVATIONS
    # =========================
    elements.append(Paragraph("Reservations", styles["Heading2"]))
    elements.append(Paragraph(str(data["shared"]["reservations"]), styles["Normal"]))
    elements.append(Spacer(1, 10))

    # =========================
    # SALES TABLE
    # =========================
    elements.append(Paragraph("Menu Sales", styles["Heading2"]))

    table_data = [["ID", "Name", "Category", "Qty", "Revenue"]]

    for s in data["shared"]["sales"]:
        table_data.append([
            s.get("id"),
            s.get("name"),
            s.get("category"),
            s.get("qty"),
            s.get("revenue")
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))

    elements.append(table)

    # =========================
    # BUILD PDF
    # =========================
    doc.build(elements)

    return send_file(file_path, as_attachment=True)

@app.route("/export-dashboard-excel")
def export_dashboard_excel():

    dashboard = build_dashboard_data() 

    wb = Workbook()

    # =========================
    # HELPERS
    # =========================
    def safe_value(v):
        if isinstance(v, str):
            return v.replace("₱", "").replace(",", "").strip()
        return v

    def auto_width(ws):
        for col in ws.columns:
            max_length = 0
            col_letter = get_column_letter(col[0].column)

            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass

            ws.column_dimensions[col_letter].width = max_length + 2

    def write_kpis(ws, kpis):
        ws.append(["KEY", "VALUE", "TREND", "POSITIVE"])

        for k, v in kpis.items():
            if isinstance(v, dict):
                ws.append([
                    str(k),
                    safe_value(v.get("value", 0)),
                    v.get("trend", "0%"),
                    v.get("positive", False)
                ])
            else:
                ws.append([str(k), safe_value(v), "", ""])

    def write_chart(ws, title, data):
        ws.append([])
        ws.append([title])
        ws.append(["Label", "Value"])

        if isinstance(data, dict):
            for l, v in zip(data.get("labels", []), data.get("data", [])):
                ws.append([l, safe_value(v)])

    # =========================
    # MAINLAND
    # =========================
    ws1 = wb.active
    ws1.title = "Mainland"

    mainland = dashboard["locations"]["mainland"]

    write_kpis(ws1, mainland["kpis"])
    write_chart(ws1, "Revenue Overview", mainland["charts"]["revenue_overview"])
    write_chart(ws1, "Weekly Sales", mainland["charts"]["weekly_sales"])
    auto_width(ws1)

    # =========================
    # FLOATING BAR
    # =========================
    ws2 = wb.create_sheet("Floating Bar")

    floating = dashboard["locations"]["floatingbar"]

    write_kpis(ws2, floating["kpis"])
    write_chart(ws2, "Revenue Overview", floating["charts"]["revenue_overview"])
    write_chart(ws2, "Weekly Sales", floating["charts"]["weekly_sales"])
    auto_width(ws2)

    # =========================
    # SHARED
    # =========================
    ws3 = wb.create_sheet("Shared Data")

    shared = dashboard["shared"]

    ws3.append(["Reservations"])
    for k, v in shared["reservations"].items():
        ws3.append([k, v])

    ws3.append([])

    ws3.append(["Sales"])
    ws3.append(["ID", "Name", "Category", "Qty", "Revenue"])

    for s in shared["sales"]:
        ws3.append([
            s.get("id"),
            s.get("name"),
            s.get("category"),
            s.get("qty"),
            safe_value(s.get("revenue"))
        ])

    ws3.append([])

    ws3.append(["Staff"])
    ws3.append(["Rank", "Name", "ID", "Role", "Guests"])

    for st in shared["staff"]:
        ws3.append([
            st.get("rank"),
            st.get("name"),
            st.get("id"),
            st.get("role"),
            st.get("guests")
        ])

    auto_width(ws3)

    file_path = "dashboard_report.xlsx"
    wb.save(file_path)

    return send_file(file_path, as_attachment=True)
@app.route("/export-dashboard-csv")
def export_dashboard_csv():

    data = build_dashboard_data() 

    file_path = "dashboard_report.csv"

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["SECTION", "TYPE", "FIELD1", "FIELD2", "FIELD3", "FIELD4"])

        # KPIs
        for k, v in data["locations"]["mainland"]["kpis"].items():
            if isinstance(v, dict):
                writer.writerow(["mainland", "kpi", k, v.get("value"), v.get("trend"), v.get("positive")])

        for k, v in data["locations"]["floatingbar"]["kpis"].items():
            if isinstance(v, dict):
                writer.writerow(["floatingbar", "kpi", k, v.get("value"), v.get("trend"), v.get("positive")])

        # SALES
        for s in data["shared"]["sales"]:
            writer.writerow([
                "shared",
                "sales",
                s.get("id"),
                s.get("name"),
                s.get("category"),
                s.get("revenue")
            ])

        # STAFF
        for st in data["shared"]["staff"]:
            writer.writerow([
                "shared",
                "staff",
                st.get("id"),
                st.get("name"),
                st.get("role"),
                st.get("guests")
            ])

    return send_file(file_path, as_attachment=True)

@app.route("/export-cash-operations-excel")
def export_cash_operations_excel():

    data = cash_operation_data_transaction()  # 

    wb = Workbook()
    ws = wb.active
    ws.title = "Cash Operations"

    # =========================
    # HEADERS
    # =========================
    headers = ["Timestamp", "Register", "Type", "Reference", "Amount", "Cashier", "Notes"]
    ws.append(headers)

    # =========================
    # WRITE DATA
    # =========================
    for row in data:
        ws.append([
            row.get("timestamp"),
            row.get("register"),
            row.get("type"),
            row.get("reference"),
            row.get("amount"),  # already formatted ₱
            row.get("cashier"),
            row.get("notes")
        ])

    # =========================
    # STYLE (BOLD HEADER)
    # =========================
    from openpyxl.styles import Font
    bold = Font(bold=True)

    for cell in ws[1]:
        cell.font = bold

    # =========================
    # AUTO COLUMN WIDTH
    # =========================
    from openpyxl.utils import get_column_letter

    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)

        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass

        ws.column_dimensions[col_letter].width = max_length + 3

    # =========================
    # SAVE FILE
    # =========================
    file_path = "cash_operations.xlsx"
    wb.save(file_path)

    return send_file(file_path, as_attachment=True)
# FLOATING_API_URL_EMPLOYEES = "http://10.104.120.221:5000/floatingbar/employees"
# FLOATING_API_URL_TRANSACTION = "http://10.104.120.221:5000/floatingbar/transaction"
# FLOATING_API_URL_TABLES = "http://10.104.120.221:5000/floatingbar/table_management"
# FLOATING_API_URL_MENU = "http://10.104.120.221:5000/floatingbar/menu"
 
GLOBAL_DATA = {
    "mainland_transactions": [],
    "floating_transactions": [],
    "menu": [],
    "drawer": [],
    "mainland_employees": [],
    "floating_employees": []
}



def load_all_data():
    GLOBAL_DATA["mainland_transactions"] = get_mainland_transaction()

    response_float = requests.get(FLOATING_API_URL_TRANSACTION)
    GLOBAL_DATA["floating_transactions"] = response_float.json()

    response_menu = requests.get(FLOATING_API_URL_MENU)
    GLOBAL_DATA["menu"] = response_menu.json()

    GLOBAL_DATA["drawer"] = get_employee_drawer_history()
    

    GLOBAL_DATA["mainland_employees"] = get_mainland_employee()

    response_float_employee = requests.get(FLOATING_API_URL_EMPLOYEES)
    GLOBAL_DATA["floating_employees"] = response_float_employee.json()
    print("Data refreshed")

def auto_refresh():
    while True:
        try:
            load_all_data()
        except Exception as e:
            print("Error refreshing data:", e)
        time.sleep(5) 


thread = threading.Thread(target=auto_refresh, daemon=True)
thread.start()

# ---------------------------------------------------------------

#                        1.) DASHBOARD

# ---------------------------------------------------------------

def get_mainland_transaction_kpis_data():
    try:
        transactions = GLOBAL_DATA["mainland_transactions"]

        current_year = datetime.now().year
        last_year = current_year - 1

        # -----------------------------
        # CURRENT YEAR VALUES
        # -----------------------------
        total_revenue = 0
        total_net = 0
        cancelled_count = 0
        active_customers = 0

        # -----------------------------
        # LAST YEAR VALUES
        # -----------------------------
        last_total_revenue = 0
        last_total_net = 0
        last_cancelled_count = 0
        last_active_customers = 0

        # -----------------------------
        # SAFE DATE PARSER
        # -----------------------------
        def parse_date(date_val):
            if not date_val:
                return None

            if isinstance(date_val, datetime):
                return date_val

            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%a, %d %b %Y %H:%M:%S %Z",
            ):
                try:
                    return datetime.strptime(date_val, fmt)
                except:
                    continue

            return None

        # -----------------------------
        # LOOP TRANSACTIONS
        # -----------------------------
        for t in transactions:
            dt = parse_date(t.get("transaction_date") or t.get("created_at"))
            if not dt:
                continue

            year = dt.year

            amount_paid = float(t.get("total_amount_paid") or 0) - float(t.get("total_change") or 0)
            amount_net = float(t.get("total_net_billing") or 0)

            status = (t.get("status") or "").lower()

            def get_pax(transaction):
                pax_count = 0

                # main guest
                main_guest = transaction.get("main_guest_information")
                if main_guest:
                    if isinstance(main_guest, str):
                        main_guest = json.loads(main_guest)
                    pax_count += 1

                # add-ons
                add_on = transaction.get("add_on_guest")
                if add_on:
                    if isinstance(add_on, str):
                        add_on = json.loads(add_on)
                    if isinstance(add_on, list):
                        pax_count += len(add_on)

                return pax_count

            pax = get_pax(t)


            if year == current_year:
                total_revenue += amount_paid
                total_net += amount_net

                if status == "cancelled":
                    cancelled_count += 1

                if status != "billout":
                    active_customers += pax

            # -----------------------------
            # LAST YEAR
            # -----------------------------
            elif year == last_year:
                last_total_revenue += amount_paid
                last_total_net += amount_net

                if status == "cancelled":
                    last_cancelled_count += 1

                if status != "billout":
                    last_active_customers += pax

        # -----------------------------
        # TREND FUNCTION
        # -----------------------------
        def get_trend(current, previous):
            if previous == 0:
                return "0%", True

            change = ((current - previous) / previous) * 100
            return f"{change:.1f}%", change >= 0

        # -----------------------------
        # COMPUTE TRENDS
        # -----------------------------
        revenue_trend, revenue_positive = get_trend(total_revenue, last_total_revenue)
        customers_trend, customers_positive = get_trend(active_customers, last_active_customers)
        cancelled_trend, cancelled_positive = get_trend(cancelled_count, last_cancelled_count)
        net_trend, net_positive = get_trend(total_net, last_total_net)

        # -----------------------------
        # RESPONSE
        # -----------------------------
        return {
            "total_revenue": {
                "value": f"₱{total_revenue:,.0f}",
                "trend": revenue_trend,
                "positive": revenue_positive
            },
            "active_customers": {
                "value": f"{active_customers:,}",
                "trend": customers_trend,
                "positive": customers_positive
            },
            "cancelled": {
                "value": f"{cancelled_count}",
                "trend": cancelled_trend,
                "positive": cancelled_positive
            },
            "net_sales": {
                "value": f"₱{total_net:,.0f}",
                "trend": net_trend,
                "positive": net_positive
            }
        }

    except Exception as e:
        print("KPI ERROR:", str(e))

        return {
            "total_revenue": {"value": "₱0", "trend": "0%", "positive": True},
            "active_customers": {"value": "0", "trend": "0%", "positive": True},
            "cancelled": {"value": "0", "trend": "0%", "positive": False},
            "net_sales": {"value": "₱0", "trend": "0%", "positive": True}
        }

def get_mainland_revenue_data():
    # transactions = get_mainland_transaction()

    transactions = GLOBAL_DATA["mainland_transactions"]

    months_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                    "November", "December"]
    
    current_month = datetime.now().month

    monthly_totals = {month:0 for month in months_order}

    for t in transactions:
        if not t.get("created_at"):
            continue

        date_obj = t["created_at"]

        if isinstance(date_obj, str):
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S")

        month_index = date_obj.month
        month_name = months_order[month_index - 1]

        if month_index > current_month:
            continue 

        amount = float(t.get("total_net_billing", 0) or 0)
        monthly_totals[month_name] += amount

    labels = months_order[:current_month]
    data = [monthly_totals[m] for m in labels]
    
    return {
        "labels" : labels,
        "data": data
    }
    

def get_mainland_weekly_data():
    # transactions = get_mainland_transaction()
    transactions = GLOBAL_DATA["mainland_transactions"]
    
    days_order = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    weekly_totals = {day: 0 for day in days_order}

    today = datetime.now()

    start_of_week = today - timedelta(days = today.weekday())
    end_of_week = start_of_week + timedelta(days = 6)

    # print("Start of Week Mainland: ", start_of_week )
    # print("End of Week Mainland: ", end_of_week)
    for t in transactions:
        if not t["created_at"]:
            continue

       
        date_obj = t["created_at"]

        # get day name (0=Mon ... 6=Sun)
        day_index = date_obj.weekday()

        if date_obj.date() < start_of_week.date() or date_obj.date() > end_of_week.date():
            continue

        # convert to Sun-Sat format
        day_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_name = day_map[day_index]

        # add sales
        # weekly_totals[day_name] += t["total_net_billing"] or 0
        amount = float(t.get("total_net_billing") or 0)
        weekly_totals[day_name] += amount

    return {
        "labels": days_order,
        "data": [weekly_totals[day] for day in days_order]
    }


def get_floatingbar_transaction_kpis_data():
    try:
        transactions = GLOBAL_DATA["floating_transactions"]

        current_year = datetime.now().year
        last_year = current_year - 1

        # -----------------------------
        # CURRENT YEAR
        # -----------------------------
        total_revenue = 0
        cancelled_count = 0
        active_customers = 0

        # -----------------------------
        # LAST YEAR
        # -----------------------------
        last_total_revenue = 0
        last_cancelled_count = 0
        last_active_customers = 0

        # -----------------------------
        # SAFE DATE PARSER
        # -----------------------------
        def parse_date(date_val):
            if not date_val:
                return None

            if isinstance(date_val, datetime):
                return date_val

            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%a, %d %b %Y %H:%M:%S %Z",
            ):
                try:
                    return datetime.strptime(date_val, fmt)
                except:
                    continue

            return None

        # -----------------------------
        # GET PAX
        # -----------------------------
        def get_pax(t):
            pax_count = 0

            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)
                pax_count += 1

            add_on = t.get("add_on_guest")
            if add_on:
                if isinstance(add_on, str):
                    add_on = json.loads(add_on)
                if isinstance(add_on, list):
                    pax_count += len(add_on)

            return pax_count

        for t in transactions:
            dt = parse_date(t.get("transaction_date") or t.get("created_at"))
            if not dt:
                continue

            year = dt.year
            amount = float(t.get("total_net_billing") or 0)
            status = (t.get("status") or "").lower()
            pax = get_pax(t)

            # CURRENT YEAR
            if year == current_year:
                total_revenue += amount

                if status == "cancelled":
                    cancelled_count += 1

                if status != "billout":
                    active_customers += pax

            # LAST YEAR
            elif year == last_year:
                last_total_revenue += amount

                if status == "cancelled":
                    last_cancelled_count += 1

                if status != "billout":
                    last_active_customers += pax

        def get_trend(current, previous):
            if previous == 0:
                return "0%", True

            change = ((current - previous) / previous) * 100
            return f"{change:.1f}%", change >= 0
            
        revenue_trend, revenue_positive = get_trend(total_revenue, last_total_revenue)
        customers_trend, customers_positive = get_trend(active_customers, last_active_customers)
        cancelled_trend, cancelled_positive = get_trend(cancelled_count, last_cancelled_count)

        net_sales = total_revenue
        net_trend, net_positive = get_trend(net_sales, last_total_revenue)

        # -----------------------------
        # RESPONSE
        # -----------------------------
        return {
            "total_revenue": {
                "value": f"₱{total_revenue:,.0f}",
                "trend": revenue_trend,
                "positive": revenue_positive
            },
            "active_customers": {
                "value": f"{active_customers:,}",
                "trend": customers_trend,
                "positive": customers_positive
            },
            "cancelled": {
                "value": f"{cancelled_count}",
                "trend": cancelled_trend,
                "positive": cancelled_positive
            },
            "net_sales": {
                "value": f"₱{net_sales:,.0f}",
                "trend": net_trend,
                "positive": net_positive
            }
        }

    except Exception as e:
        print("KPI ERROR:", str(e))

        return {
            "total_revenue": {"value": "₱0", "trend": "0%", "positive": True},
            "active_customers": {"value": "0", "trend": "0%", "positive": True},
            "cancelled": {"value": "0", "trend": "0%", "positive": False},
            "net_sales": {"value": "₱0", "trend": "0%", "positive": True}
        }

def get_floatingbar_weekly_data():
    try:
        # print("calling api floating transaction")
        # response = requests.get(FLOATING_API_URL_TRANSACTION)
        # result = response.json()

        # # print(result)
       
        # transactions = result
        transactions = GLOBAL_DATA["floating_transactions"]
        today = datetime.now()

        
        start_of_week = today - timedelta(days=today.weekday())

    
        end_of_week = start_of_week + timedelta(days=6)

        # print("Start of week:", start_of_week)
        # print("End of week:", end_of_week)

        days_order = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        weekly_totals = {day: 0 for day in days_order}

        for t in transactions:
            if not t.get("created_at"):
                continue

            date_obj = datetime.strptime(t["created_at"], "%a, %d %b %Y %H:%M:%S %Z")
            
            day_index = date_obj.weekday()

            if date_obj.date() < start_of_week.date() or date_obj.date() > end_of_week.date():
                continue
    
            day_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_name = day_map[day_index]

          
            # weekly_totals[day_name] += t.get("total_net_billing", 0)
            amount = float(t.get("total_net_billing") or 0)
            weekly_totals[day_name] += amount

        return {
            "labels": days_order,
            "data": [weekly_totals[day] for day in days_order]
        }

    except Exception as e:
        print("Error:", e)
        return {
            "labels": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            "data": [0, 0, 0, 0, 0, 0, 0]
        }
    
def get_floatingbar_revenue_data():
    try:
        # print("floatingbar revenue data")
        # response = requests.get(FLOATING_API_URL_TRANSACTION)
        # result = response.json()
        # transactions = result
        # print(transactions)
        transactions = GLOBAL_DATA["floating_transactions"]
        
        months_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                    "November", "December"]
        
        current_month = datetime.now().month

        monthly_totals = {month:0 for month in months_order }

        for t in transactions:
            if not t.get("created_at"):
                continue
            date_obj = datetime.strptime(t["created_at"], "%a, %d %b %Y %H:%M:%S %Z")

            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj,  "%Y-%m-%d %H:%M:%S")

            month_index = date_obj.month
            month_name = months_order[month_index - 1]

            if month_index > current_month:
                continue

            amount = float(t.get("total_net_billing", 0) or 0 )
            monthly_totals[month_name] += amount
        labels = months_order[:current_month]
        data = [monthly_totals[m] for m in labels]

        return{
            "labels": labels,
            "data": data
        }


    except Exception as e:
        print("Error", e)
        return {"status": "error", "message": str(e)}, 400
    
def get_shared_menu_sales_data():
    try:


        # response_menu = requests.get(FLOATING_API_URL_MENU)
        # menu = response_menu.json()
        menu = GLOBAL_DATA["menu"]

        # response_transactions = requests.get(FLOATING_API_URL_TRANSACTION)
        # transactions = response_transactions.json()
        transactions = GLOBAL_DATA["floating_transactions"]


        menu_map = {}

        
        for m in menu:
            name = m.get("menu_name")
            category = m.get("category", "Unknown")

            if name:
                menu_map[name] = category


        sales_map = {}

        for t in transactions:

            # MAIN GUEST
            main_guest = t.get("main_guest_information")

            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                services = main_guest.get("services_availed", [])

                for item in services:
                    if item.get("is_void") is True:
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)
                    price = float(item.get("price") or 0)

                    if not name:
                        continue

                    if name not in sales_map:
                        sales_map[name] = {
                            "name": name,
                            "qty": 0,
                            "price": price,
                            "revenue": 0
                        }

                    sales_map[name]["qty"] += qty
                    sales_map[name]["revenue"] += qty * price

            # ADD-ON GUESTS
            add_on_guests = t.get("add_on_guest")

            if add_on_guests:
                if isinstance(add_on_guests, str):
                    add_on_guests = json.loads(add_on_guests)

                if isinstance(add_on_guests, list):
                    for guest in add_on_guests:
                        services = guest.get("services_availed", [])

                        for item in services:
                            if item.get("is_void") is True:
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)
                            price = float(item.get("price") or 0)

                            if not name:
                                continue

                            if name not in sales_map:
                                sales_map[name] = {
                                    "name": name,
                                    "qty": 0,
                                    "price": price,
                                    "revenue": 0
                                }

                            sales_map[name]["qty"] += qty
                            sales_map[name]["revenue"] += qty * price


        sales_list = []
        index = 1

        for item_name, data in sales_map.items():

           
            category = menu_map.get(item_name, "Unknown")

            sales_list.append({
                "id": f"ITEM{index:03}",
                "name": data["name"],
                "category": category, 
                "qty": data["qty"],
                "price": f"₱{data['price']:.2f}",
                "revenue": f"₱{data['revenue']:,.2f}",
                "trend": "+0%",
                "positive": True
            })
            index += 1

        return sales_list

    except Exception as e:
        print("SALES ERROR:", str(e))
        return []

def get_shared_reservation_data():
    try:
        transactions = get_transaction_reserved()

        reserved = 0
        awaiting = 0
        checked_in = 0

    
        for t in transactions:
            reserved += 1 

            status = (t.get("status") or "").lower()

            if status == "pending":
                awaiting += 1
            elif status == "confirmed":
                checked_in += 1

        # print(reserved)
        # print(awaiting)
        # print(checked_in)
            
        return {
         
                "reserved": str(reserved),
                "awaiting": str(awaiting),
                "checked_in": str(checked_in)
            
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_shared_employee_rank_data():
    try:
        # mainland_transactions = get_mainland_transaction()
        mainland_transactions = GLOBAL_DATA["mainland_transactions"]

        # response_float_transaction = requests.get(FLOATING_API_URL_TRANSACTION)
        # floating_transactions = response_float_transaction.json()
        floating_transactions = GLOBAL_DATA["floating_transactions"]

        staff_count = defaultdict(int)


        for t in mainland_transactions:
            staff = t.get("attended_by")

            if staff and staff not in ["N/A", "Staff"]:
                staff_count[staff.strip()] += 1

        for t in floating_transactions:

      
            main_guest = t.get("main_guest_information")

            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                for item in main_guest.get("services_availed", []):
                    if item.get("is_void"):
                        continue

                    waiter = item.get("waiter")

                    if waiter and waiter not in ["N/A", "Staff"]:
                        staff_count[waiter.strip()] += 1

            # ADD-ON GUESTS
            add_on = t.get("add_on_guest")

            if add_on:
                if isinstance(add_on, str):
                    add_on = json.loads(add_on)

                if isinstance(add_on, list):
                    for guest in add_on:
                        for item in guest.get("services_availed", []):
                            if item.get("is_void"):
                                continue

                            waiter = item.get("waiter")

                            if waiter and waiter not in ["N/A", "Staff"]:
                                staff_count[waiter.strip()] += 1


        sorted_staff = sorted(
            staff_count.items(),
            key=lambda x: x[1],
            reverse=True
        )

        staff_list = []
        for i, (name, count) in enumerate(sorted_staff, start=1):
            staff_list.append({
                "rank": str(i),
                "name": name,
                "id": f"S{i:03}",
                "role": "Staff",  
                "guests": count,
                "present": count,   
                "absences": 0,
                "trend": "+0%",
                "positive": True
            })

        return staff_list

    except Exception as e:
        print("EMPLOYEE ERROR:", str(e))
        return []


DASHBOARD_DATA = {
    "locations": {
        "mainland": {
            # "kpis": {
            #     "total_revenue": {"value": "₱49,064", "trend": "+20.1%", "positive": True},
            #     "active_customers": {"value": "2,015", "trend": "+12.5%", "positive": True},
            #     "cancelled": {"value": "23", "trend": "-3.2%", "positive": False},
            #     "net_sales": {"value": "₱43,750", "trend": "+15.8%", "positive": True}
            # },
            "kpis": get_mainland_transaction_kpis_data(),
            "charts": {
                # "revenue_overview": {
                #     "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                #     "data": [4000, 3000, 5000, 4500, 6000, 5500]
                # },
                "revenue_overview" : get_mainland_revenue_data(),
                # "weekly_sales": {
                #     "labels": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                #     "data": [8000, 12000, 15000, 14000, 18000, 21000, 20000]
                # }
                "weekly_sales":  get_mainland_weekly_data()
            }
        },
        "floatingbar": {
            # "kpis": {
            #     "total_revenue": {"value": "₱62,450", "trend": "+24.3%", "positive": True},
            #     "active_customers": {"value": "1,842", "trend": "+18.7%", "positive": True},
            #     "cancelled": {"value": "15", "trend": "-5.8%", "positive": False},
            #     "net_sales": {"value": "₱56,320", "trend": "+22.4%", "positive": True}
            # },
            "kpis": get_floatingbar_transaction_kpis_data(),
            "charts": {
                # "revenue_overview": {
                #     "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                #     "data": [3200, 3800, 4200, 5000, 5800, 6400]
                # },
                "revenue_overview": get_floatingbar_revenue_data(),

                # "weekly_sales": {
                #     "labels": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                #     "data": [6500, 9500, 11000, 13000, 16000, 25000, 22000]
                # }
                "weekly_sales": get_floatingbar_weekly_data()
            }
        }
    },
    "shared": {
        # "reservations": {
        #     "reserved": "156",
        #     "awaiting": "43",
        #     "checked_in": "89"
        # },
        "reservations": get_shared_reservation_data(),
        # "sales": [
        #     {"id": "F001", "name": "Lobster Thermidor", "category": "Food", "qty": 156, "price": "₱42.99", "revenue": "₱6,706.44", "trend": "+12%", "positive": True},
        #     {"id": "F002", "name": "Surf and Turf Burger", "category": "Food", "qty": 342, "price": "₱28.50", "revenue": "₱9,747.00", "trend": "+18%", "positive": True},
        #     {"id": "F003", "name": "Carbonara Oceanica", "category": "Food", "qty": 124, "price": "₱32.99", "revenue": "₱4,090.76", "trend": "+8%", "positive": True},
        #     {"id": "BV001", "name": "Cosmopolitan", "category": "Beverage", "qty": 167, "price": "₱16.99", "revenue": "₱2,837.33", "trend": "+9%", "positive": True}
        # ],

        "sales": get_shared_menu_sales_data(),
        # "staff": [
        #     {"rank": "1", "name": "Arjunren Valdez", "id": "S001", "role": "Head Waiter", "guests": 342, "present": 22, "absences": 0, "trend": "+12%", "positive": True},
        #     {"rank": "2", "name": "Elon Ybrahim Sobrevilla", "id": "S002", "role": "Senior Waiter", "guests": 318, "present": 21, "absences": 1, "trend": "+8%", "positive": True},
        #     {"rank": "3", "name": "Anthony Aldrin Beltran", "id": "S003", "role": "Waiter", "guests": 295, "present": 20, "absences": 2, "trend": "+15%", "positive": True}
        # ]
        "staff": get_shared_employee_rank_data()
    }
}

@app.route("/")
def login():
    session.clear()
    return render_template("index.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route("/mainland/login", methods=["POST"])
def login_route():
    # Get data from JSON or form
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    employee_id = data.get("employee_id")
    password = data.get("password")

    if not employee_id or not password:
        return jsonify({"success": False, "message": "Invalid Credentials"}), 400

    # Replace this with your real login function
    user = mainland_employee_login(employee_id, password)
    
    if not user or user.get('position')=='waiter' or user.get('position') == 'cashier':
        return jsonify({"success": False, "message": "Invalid User Access"}), 401

    # Store user info in session instead of creating JWT
    session['employee_id'] = user["employee_id"]
    session['position'] = user.get("position", "staff")
    session['name'] = f"{user.get('firstName')} {user.get('lastName')}"

    return jsonify({
        "success": True,
        "position": session['position'],
        "name": session['name']
    }), 200


@app.route('/dashboard')
def index():
    current_date = datetime.now().strftime("%B %Y")
    
    return render_template('dashboard.html', current_date=current_date, session=session)

@app.route('/api/data')
def get_data():
    return jsonify({
        "locations": {
            "mainland": {
                "kpis": get_mainland_transaction_kpis_data(),
                "charts": {
                    "revenue_overview": get_mainland_revenue_data(),
                    "weekly_sales": get_mainland_weekly_data()
                }
            },
            "floatingbar": {
                "kpis": get_floatingbar_transaction_kpis_data(),
                "charts": {
                    "revenue_overview": get_floatingbar_revenue_data(),
                    "weekly_sales": get_floatingbar_weekly_data()
                }
            }
        },
        "shared": {
            "reservations": get_shared_reservation_data(),
            "sales": get_shared_menu_sales_data(),
            "staff": get_shared_employee_rank_data()
        }
    })

# -----------------------------------------------------

#                    2.) SALES OVERVIEW

# -----------------------------------------------------

def get_kpis_sales_data_overview():
    try:

        #babalikan
        mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])

        # response = requests.get(FLOATING_API_URL_TRANSACTION)
        floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

        all_transactions = mainland_transactions + floating_transactions

        # ---------------------------
        # METRICS
        # ---------------------------
        total_revenue = 0
        total_orders = 0
        active_customers = 0

        for t in all_transactions:

            # ---------------------------
            # TOTAL REVENUE
            # ---------------------------
            revenue = t.get("total_net_billing") or 0
            try:
                total_revenue += float(revenue)
            except:
                pass

            # ---------------------------
            # MAIN GUEST (1 pax)
            # ---------------------------
            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                active_customers += 1

                services = main_guest.get("services_availed", [])

                for item in services:
                    if item.get("is_void") is True:
                        continue

                    qty = int(item.get("qty") or 0)
                    total_orders += qty

            # ---------------------------
            # ADD-ON GUESTS
            # ---------------------------
            add_on_guests = t.get("add_on_guest")

            if add_on_guests:
                if isinstance(add_on_guests, str):
                    add_on_guests = json.loads(add_on_guests)

                if isinstance(add_on_guests, list):

                    # COUNT CUSTOMERS
                    active_customers += len(add_on_guests)

                    for guest in add_on_guests:
                        services = guest.get("services_availed", [])

                        for item in services:
                            if item.get("is_void") is True:
                                continue

                            qty = int(item.get("qty") or 0)
                            total_orders += qty

        # ---------------------------
        # AOV
        # ---------------------------
        aov = total_revenue / total_orders if total_orders > 0 else 0

        # ---------------------------
        # OUTPUT
        # ---------------------------
        return {
            
                "total_revenue": {
                    "value": f"₱{total_revenue:,.0f}",
                    "trend": "0%",
                    "positive": True
                },
                "total_orders": {
                    "value": f"{total_orders:,}",
                    "trend": "0%",
                    "positive": True
                },
                "aov": {
                    "value": f"₱{aov:,.2f}",
                    "trend": "0%",
                    "positive": True
                },
                "customers": {
                    "value": f"{active_customers:,}",
                    "trend": "0%",
                    "positive": True
                }
            
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_category_sales_data():
    try:
        #babalikan
        # response_menu = requests.get(FLOATING_API_URL_MENU)
        menu = GLOBAL_DATA.get("menu", [])

        # response_transactions = requests.get(FLOATING_API_URL_TRANSACTION)
        transactions = GLOBAL_DATA.get("floating_transactions", [])

        menu_map = {}
        type_map = {}

        for m in menu:
            name = m.get("menu_name")
            category = (m.get("category") or "").lower()
            item_type = (m.get("type") or "").lower()

            if name:
                menu_map[name] = category
                type_map[name] = item_type

        category_count = {
            "Food": 0,
            "Beer": 0,
            "Beverages": 0
        }

        current_month = datetime.now().month

        for t in transactions:

            created_at = t.get("created_at")
            if not created_at:
                continue

            if isinstance(created_at, str):
                try:
                    date_obj = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        date_obj = datetime.strptime(created_at, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        continue
            else:
                continue

            if date_obj.month != current_month:
                continue

            # ---------------- MAIN GUEST ----------------
            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                services = main_guest.get("services_availed", [])

                for item in services:
                    if item.get("is_void") is True:
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue

                    category = menu_map.get(name, "")
                    item_type = type_map.get(name, "")

                    cat_lower = category.lower()

                    if "beer" in cat_lower:
                        main_category = "Beer"

                    elif item_type == "drinkable" or any(x in cat_lower for x in [
                        "cocktails", "mocktails", "juice", "coffee", "tea",
                        "sodas", "water", "gin", "vodka", "tequila", "rum",
                        "whisky", "whiskey", "bourbon", "cognac", "brandy",
                        "wine", "champagne"
                    ]):
                        main_category = "Beverages"

                    else:
                        main_category = "Food"

                    category_count[main_category] += qty

            # ---------------- ADD-ON GUESTS ----------------
            add_on_guests = t.get("add_on_guest")
            if add_on_guests:
                if isinstance(add_on_guests, str):
                    add_on_guests = json.loads(add_on_guests)

                if isinstance(add_on_guests, list):
                    for guest in add_on_guests:
                        services = guest.get("services_availed", [])

                        for item in services:
                            if item.get("is_void") is True:
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            category = menu_map.get(name, "")
                            item_type = type_map.get(name, "")

                            cat_lower = category.lower()

                            if "beer" in cat_lower:
                                main_category = "Beer"

                            elif item_type == "drinkable" or any(x in cat_lower for x in [
                                "cocktails", "mocktails", "juice", "coffee", "tea",
                                "sodas", "water", "gin", "vodka", "tequila", "rum",
                                "whisky", "whiskey", "bourbon", "cognac", "brandy",
                                "wine", "champagne"
                            ]):
                                main_category = "Beverages"

                            else:
                                main_category = "Food"

                            category_count[main_category] += qty

        labels = ["Food", "Beer", "Beverages"]
        data = [category_count[l] for l in labels]

        return {
            "labels": labels,
            "data": data,
            "colors": ["#8b5cf6", "#f59e0b", "#3b82f6"]
        }

    except Exception as e:
        print("CATEGORY ERROR:", str(e))
        return {"status": "error", "message": str(e)}, 400


def get_category_performance_data():
    try:
        menu = GLOBAL_DATA.get("menu", [])
        transactions = GLOBAL_DATA.get("floating_transactions", [])

        # ---------------------------
        # MENU MAP
        # ---------------------------
        menu_map = {}
        type_map = {}

        for m in menu:
            name = m.get("menu_name")
            category = (m.get("category") or "").lower()
            item_type = (m.get("type") or "").lower()

            if name:
                menu_map[name] = category
                type_map[name] = item_type

        # ---------------------------
        # CATEGORY REVENUE
        # ---------------------------
        category_performance_sale = {
            "Food": 0,
            "Beer": 0,
            "Beverages": 0
        }

        current_month = datetime.now().month

        # ---------------------------
        # PROCESS TRANSACTIONS
        # ---------------------------
        for t in transactions:

            created_at = t.get("created_at")
            if not created_at:
                continue

            # parse date
            if isinstance(created_at, str):
                try:
                    date_obj = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        date_obj = datetime.strptime(created_at, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        continue
            else:
                continue

            if date_obj.month != current_month:
                continue

            # ---------------- MAIN GUEST ----------------
            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                services = main_guest.get("services_availed", [])

                for item in services:
                    if item.get("is_void") is True:
                        continue

                    name = item.get("item")
                    if not name:
                        continue

                    qty = abs(int(item.get("qty") or 0))
                    price = abs(float(item.get("price") or 0))

                    amount = qty * price

                    category = menu_map.get(name, "")
                    item_type = type_map.get(name, "")

                    cat_lower = (category or "").lower()

                    if "beer" in cat_lower:
                        main_category = "Beer"

                    elif item_type == "drinkable" or any(x in cat_lower for x in [
                        "cocktails", "mocktails", "juice", "coffee", "tea",
                        "sodas", "water", "gin", "vodka", "tequila", "rum",
                        "whisky", "whiskey", "bourbon", "cognac", "brandy",
                        "wine", "champagne"
                    ]):
                        main_category = "Beverages"

                    else:
                        main_category = "Food"

                    category_performance_sale[main_category] += amount

            # ---------------- ADD-ON GUESTS ----------------
            add_on_guests = t.get("add_on_guest")
            if add_on_guests:
                if isinstance(add_on_guests, str):
                    add_on_guests = json.loads(add_on_guests)

                if isinstance(add_on_guests, list):
                    for guest in add_on_guests:
                        services = guest.get("services_availed", [])

                        for item in services:
                            if item.get("is_void") is True:
                                continue

                            name = item.get("item")
                            if not name:
                                continue

                            qty = abs(int(item.get("qty") or 0))
                            price = abs(float(item.get("price") or 0))

                            amount = qty * price

                            category = menu_map.get(name, "")
                            item_type = type_map.get(name, "")

                            cat_lower = (category or "").lower()

                            if "beer" in cat_lower:
                                main_category = "Beer"

                            elif item_type == "drinkable" or any(x in cat_lower for x in [
                                "cocktails", "mocktails", "juice", "coffee", "tea",
                                "sodas", "water", "gin", "vodka", "tequila", "rum",
                                "whisky", "whiskey", "bourbon", "cognac", "brandy",
                                "wine", "champagne"
                            ]):
                                main_category = "Beverages"

                            else:
                                main_category = "Food"

                            category_performance_sale[main_category] += amount

        # ---------------------------
        # TOTAL + PERCENT
        # ---------------------------
        total = sum(category_performance_sale.values())

        color_map = {
            "Food": "bg-purple-500",
            "Beer": "bg-orange-500",
            "Beverages": "bg-blue-500"
        }

        result = []

        for category in ["Food", "Beer", "Beverages"]:
            revenue = category_performance_sale[category]
            percent = (revenue / total * 100) if total > 0 else 0

            result.append({
                "name": category,
                "revenue": f"₱{revenue:,.0f}",
                "percent": f"{percent:.1f}%",
                "color": color_map[category]
            })

        return result

    except Exception as e:
        print("CATEGORY PERFORMANCE ERROR:", str(e))
        return []
    
def get_combined_revenue_data_sales():
    try:
        mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])

        # response = requests.get(FLOATING_API_URL_TRANSACTION)
        floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

        # ---------------------------
        # COMBINE DATA FIRST
        # ---------------------------
        all_transactions = mainland_transactions + floating_transactions

        months_order = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        now = datetime.now()
        current_year = now.year
        current_month = now.month

        monthly_totals = {month: 0 for month in months_order}

        for t in all_transactions:
            if not t.get("created_at"):
                continue

            date_obj = t["created_at"]

            # Parse date if string
            if isinstance(date_obj, str):
                try:
                    date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        date_obj = datetime.strptime(date_obj, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        continue

            # ✅ Only include current year
            if date_obj.year != current_year:
                continue

            month_name = months_order[date_obj.month - 1]
            amount = float(t.get("total_net_billing", 0) or 0)

            monthly_totals[month_name] += amount

 
        labels = months_order[:current_month]
        data = [monthly_totals[m] for m in labels]

        return {
            "labels": labels,
            "data": data
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {"status": "error", "message": str(e)}, 400
    
def get_shared_menu_sales_data_overview():
    try:
        #babalikan

        # response_menu = requests.get(FLOATING_API_URL_MENU)
        menu = GLOBAL_DATA.get("menu", [])

        # response_transactions = requests.get(FLOATING_API_URL_TRANSACTION)
        transactions = GLOBAL_DATA.get("floating_transactions", [])

        # ---------------------------
        # MENU MAP
        # ---------------------------
        menu_map = {}

        for m in menu:
            name = m.get("menu_name")
            category = m.get("category", "Unknown")

            if name:
                menu_map[name] = category

        # ---------------------------
        # SALES MAP
        # ---------------------------
        sales_map = {}

        for t in transactions:

            main_guest = t.get("main_guest_information")

            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                services = main_guest.get("services_availed", [])

                for item in services:
                    if item.get("is_void") is True:
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)
                    price = float(item.get("price") or 0)

                    if not name:
                        continue

                    if name not in sales_map:
                        sales_map[name] = {
                            "name": name,
                            "category": menu_map.get(name, "Unknown"),
                            "qty": 0,
                            "revenue": 0
                        }

                    sales_map[name]["qty"] += qty
                    sales_map[name]["revenue"] += qty * price

            add_on_guests = t.get("add_on_guest")

            if add_on_guests:
                if isinstance(add_on_guests, str):
                    add_on_guests = json.loads(add_on_guests)

                if isinstance(add_on_guests, list):
                    for guest in add_on_guests:
                        services = guest.get("services_availed", [])

                        for item in services:
                            if item.get("is_void") is True:
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)
                            price = float(item.get("price") or 0)

                            if not name:
                                continue

                            if name not in sales_map:
                                sales_map[name] = {
                                    "name": name,
                                    "category": menu_map.get(name, "Unknown"),
                                    "qty": 0,
                                    "revenue": 0
                                }

                            sales_map[name]["qty"] += qty
                            sales_map[name]["revenue"] += qty * price

        # ---------------------------
        # SORT BY REVENUE
        # ---------------------------
        sorted_items = sorted(
            sales_map.values(),
            key=lambda x: x["revenue"],
            reverse=True
        )

        # ---------------------------
        # FORMAT OUTPUT (MATCH YOUR SAMPLE EXACTLY)
        # ---------------------------
        top_items = []

        for i, item in enumerate(sorted_items[:10], start=1):
            top_items.append({
                "rank": i,
                "name": item["name"],
                "category": item["category"],
                "units": f"{item['qty']:,}",   
                "revenue": f"₱{item['revenue']:,.2f}",
                "growth": "0%"  
            })

        return top_items

    except Exception as e:
        print("SALES ERROR:", str(e))
        return []

    
SALES_OVERVIEW_DATA = {
    # "kpis": {
    #     "total_revenue": {"value": "₱391,379", "trend": "+16.4%", "positive": True},
    #     "total_orders": {"value": "14,619", "trend": "+12.8%", "positive": True},
    #     "aov": {"value": "₱26.77", "trend": "+3.2%", "positive": True},
    #     "customers": {"value": "10,845", "trend": "+8.7%", "positive": True}
    # },
    "kpis": get_kpis_sales_data_overview(),
    "charts": {
        # "monthly_trend": {
        #     "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        #     "data": [72000, 85000, 78000, 95000, 88000, 92000]
        # },
        "monthly_trend": get_combined_revenue_data_sales(),
        # "category_distribution": {
        #     "labels": ["Food", "Beer", "Beverages"],
        #     "data": [55, 33, 13],
        #     "colors": ["#8b5cf6", "#f59e0b", "#3b82f6"]
        # }
        "category_distribution": get_category_sales_data()
    },
    # "category_performance": [
    #     {"name": "Food", "revenue": "₱319,000", "percent": "54.5%", "color": "bg-purple-500"},
    #     {"name": "Beer", "revenue": "₱191,000", "percent": "32.6%", "color": "bg-orange-500"},
    #     {"name": "Beverages", "revenue": "₱75,000", "percent": "12.8%", "color": "bg-blue-500"}
    # ],
    "category_performance" : get_category_performance_data(),
    # "top_items": [
    #     {"rank": 1, "name": "Lobster Thermidor", "category": "Food", "units": "1,247", "revenue": "₱53,619.53", "growth": "+18%"},
    #     {"rank": 2, "name": "Surf and Turf Burger", "category": "Food", "units": "2,156", "revenue": "₱61,446.00", "growth": "+22%"},
    #     {"rank": 3, "name": "Carbonara Oceanica", "category": "Food", "units": "982", "revenue": "₱32,396.18", "growth": "+15%"},
    #     {"rank": 4, "name": "Chirachi Sashimi Pizza", "category": "Food", "units": "1,893", "revenue": "₱51,093.07", "growth": "+12%"},
    #     {"rank": 5, "name": "Salmon Poke", "category": "Food", "units": "1,654", "revenue": "₱41,325.46", "growth": "+10%"},
    #     {"rank": 6, "name": "Tuna Crudo", "category": "Food", "units": "1,432", "revenue": "₱32,922.68", "growth": "+14%"},
    #     {"rank": 7, "name": "Beetroot Hummus", "category": "Food", "units": "1,821", "revenue": "₱27,302.79", "growth": "+8%"},
    #     {"rank": 8, "name": "Coconut Mousse", "category": "Food", "units": "876", "revenue": "₱11,378.24", "growth": "+5%"},
    #     {"rank": 9, "name": "Cosmopolitan", "category": "Beverage", "units": "1,245", "revenue": "₱21,153.55", "growth": "+11%"},
    #     {"rank": 10, "name": "Port Barton Sunset", "category": "Beverage", "units": "987", "revenue": "₱18,742.13", "growth": "+16%"}
    # ]
    "top_items": get_shared_menu_sales_data_overview()
}

@app.route('/sales-overview')
def sales_overview():
    current_date = datetime.now().strftime("%B %Y")
    return render_template('sales_overview.html', current_date = current_date)

@app.route('/api/sales-overview')
def get_sales_data():
    data = {
        "kpis": get_kpis_sales_data_overview(),
        "charts": {
            "monthly_trend": get_combined_revenue_data_sales(),
            "category_distribution": get_category_sales_data()
        },
        "category_performance": get_category_performance_data(),
        "top_items": get_shared_menu_sales_data_overview()
    }


    return jsonify(data)

# ----------------------------------------------

#                3.) REVENEU STREAMS

# ----------------------------------------------

def get_combined_revenue_data():
    mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])
    floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    current_month = datetime.now().month

    mainland_totals = {month: 0 for month in months_order}
    floating_totals = {month: 0 for month in months_order}


    # print(floating_transactions)
    # print(mainland_transactions)
    for t in mainland_transactions:
        date_val = t.get("created_at")
        if not date_val:
            continue

        if isinstance(date_val, str):
            try:
                date_obj = datetime.strptime(date_val, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    date_obj = datetime.strptime(date_val, "%a, %d %b %Y %H:%M:%S %Z")
                except:
                    continue
        else:
            date_obj = date_val

        if date_obj.month > current_month:
            continue

        month_name = months_order[date_obj.month - 1]
        mainland_totals[month_name] += float(t.get("total_net_billing", 0))


    for t in floating_transactions:
        date_val = t.get("created_at")
        if not date_val:
            continue

        if isinstance(date_val, str):
            try:
                date_obj = datetime.strptime(date_val, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    date_obj = datetime.strptime(date_val, "%a, %d %b %Y %H:%M:%S %Z")
                except:
                    continue
        else:
            date_obj = date_val

        if date_obj.month > current_month:
            continue

        month_name = months_order[date_obj.month - 1]
        floating_totals[month_name] += float(t.get("total_net_billing", 0) or 0)

    labels = months_order[:current_month]

    mainland_data = [mainland_totals[m] for m in labels]
    floating_data = [floating_totals[m] for m in labels]

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Mainland",
                "data": mainland_data,
                "borderColor": "#8b5cf6",
                "backgroundColor": "transparent"
            },
            {
                "label": "Skydeck",
                "data": floating_data,
                "borderColor": "#f59e0b",
                "backgroundColor": "transparent"
            }
        ]
    }


def get_last_7_days_revenue():
    mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])
    floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

    
    days_order = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    mainland_totals = {day: 0 for day in days_order}
    skydeck_totals = {day: 0 for day in days_order}
    maindeck_totals = {day: 0 for day in days_order}

    def parse_date(date_val):
        if isinstance(date_val, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S %Z"):
                try:
                    return datetime.strptime(date_val, fmt)
                except:
                    continue
            return None
        return date_val

   
    for t in mainland_transactions:
        date_obj = parse_date(t.get("created_at"))
        if not date_obj:
            continue

        day_name = date_obj.strftime("%a")  # Mon, Tue, etc.
        amount = float(t.get("total_net_billing", 0) or 0)

        if day_name in mainland_totals:
            mainland_totals[day_name] += amount

   
    for t in floating_transactions:
        date_obj = parse_date(t.get("created_at"))
        if not date_obj:
            continue

        day_name = date_obj.strftime("%a")
        amount = float(t.get("total_net_billing", 0) or 0 )

        deck = t.get("deck_assigned", "").strip().lower().replace(" ", "")

        if deck == "skydeck" and day_name in skydeck_totals:
            skydeck_totals[day_name] += amount
        elif deck == "maindeck" and day_name in maindeck_totals:
            maindeck_totals[day_name] += amount

    return {
        "labels": days_order,
        "datasets": [
            {
                "label": "Mainland",
                "data": [mainland_totals[d] for d in days_order],
                "backgroundColor": "#8b5cf6"
            },
            {
                "label": "Skydeck",
                "data": [skydeck_totals[d] for d in days_order],
                "backgroundColor": "#f59e0b"
            },
            {
                "label": "Maindeck",
                "data": [maindeck_totals[d] for d in days_order],
                "backgroundColor": "#10b981"
            }
        ]
    }

# def get_last_7_days_revenue():
#     mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])
#     floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

#     today = datetime.now().date()

#     days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
#     labels = [d.strftime("%b %d") for d in days]

#     mainland_totals = {d: 0 for d in days}
#     skydeck_totals = {d: 0 for d in days}
#     maindeck_totals = {d: 0 for d in days}

  
#     for t in mainland_transactions:
#         date_val = t.get("created_at")
#         if not date_val:
#             continue

#         if isinstance(date_val, str):
#             try:
#                 date_obj = datetime.strptime(date_val, "%Y-%m-%d %H:%M:%S")
#             except:
#                 try:
#                     date_obj = datetime.strptime(date_val, "%a, %d %b %Y %H:%M:%S %Z")
#                 except:
#                     continue
#         else:
#             date_obj = date_val

#         date_only = date_obj.date()

#         if date_only not in mainland_totals:
#             continue

#         mainland_totals[date_only] += float(t.get("total_net_billing", 0))

#     for t in floating_transactions:
#         date_val = t.get("created_at")
#         if not date_val:
#             continue

#         if isinstance(date_val, str):
#             try:
#                 date_obj = datetime.strptime(date_val, "%Y-%m-%d %H:%M:%S")
#             except:
#                 try:
#                     date_obj = datetime.strptime(date_val, "%a, %d %b %Y %H:%M:%S %Z")
#                 except:
#                     continue
#         else:
#             date_obj = date_val

#         date_only = date_obj.date()

#         if date_only not in skydeck_totals:
#             continue

#         amount = float(t.get("total_net_billing", 0))
#         deck = t.get("deck_assigned", "").lower()

#         if deck == "skydeck":
#             skydeck_totals[date_only] += amount
#         elif deck == "maindeck":
#             maindeck_totals[date_only] += amount

#     mainland_data = [mainland_totals[d] for d in days]
#     skydeck_data = [skydeck_totals[d] for d in days]
#     maindeck_data = [maindeck_totals[d] for d in days]

#     return {
#         "labels": labels,
#         "datasets": [
#             {
#                 "label": "Mainland",
#                 "data": mainland_data,
#                 "backgroundColor": "#8b5cf6"
#             },
#             {
#                 "label": "Skydeck",
#                 "data": skydeck_data,
#                 "backgroundColor": "#f59e0b"
#             },
#             {
#                 "label": "Maindeck",
#                 "data": maindeck_data,
#                 "backgroundColor": "#10b981"
#             }
#         ]
#     }
# ----------------------------
# SAFE DATE PARSER (FIXED)
# ----------------------------
def parse_date(date_val):
    if not date_val:
        return None

    if isinstance(date_val, datetime):
        return date_val.replace(hour=0, minute=0, second=0, microsecond=0)

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %Z",
    ):
        try:
            dt = datetime.strptime(date_val, fmt)

            # ✅ FORCE DATE ONLY (prevents April 8 → April 9 issue)
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

        except:
            continue

    return None


# ----------------------------
# DISTRIBUTION DATA
# ----------------------------
def get_distribution_data(view="month", start=None, end=None):
    mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])
    floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

    now = datetime.now()

    start_obj = parse_date(start) if start else None
    end_obj = parse_date(end) if end else None

    if end_obj:
        end_obj = end_obj.replace(hour=23, minute=59, second=59)

    mainland_total = 0
    skydeck_total = 0
    maindeck_total = 0

    def is_valid(t):
        date_obj = parse_date(t.get("created_at"))
        if not date_obj:
            return False

        # RANGE
        if start_obj and end_obj:
            return start_obj.date() <= date_obj.date() <= end_obj.date()

        # SINGLE DATE
        if start_obj and not end_obj:
            return date_obj.date() == start_obj.date()

        # MONTH
        if view == "month":
            return date_obj.year == now.year and date_obj.month == now.month

        # WEEK
        elif view == "week":
            start_week = now - timedelta(days=now.weekday())
            return date_obj.date() >= start_week.date()

        # DAY
        elif view == "day":
            return date_obj.date() == now.date()

        return True

    # MAINLAND
    for t in mainland_transactions:
        if not is_valid(t):
            continue
        mainland_total += float(t.get("total_net_billing") or 0)

    # FLOATING
    for t in floating_transactions:
        if not is_valid(t):
            continue

        amount = float(t.get("total_net_billing") or 0)
        deck = (t.get("deck_assigned") or "").strip().lower().replace(" ", "")

        if deck == "skydeck":
            skydeck_total += amount
        elif deck == "maindeck":
            maindeck_total += amount

    return {
        "labels": ["Mainland", "Skydeck", "Maindeck"],
        "data": [mainland_total, skydeck_total, maindeck_total],
        "colors": ["#8b5cf6", "#f59e0b", "#10b981"]
    }


# ----------------------------
# KPI DATA
# ----------------------------
def get_kpis_base_revenue_data(view="month", start=None, end=None):
    mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])
    floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

    now = datetime.now()

    start_obj = parse_date(start) if start else None
    end_obj = parse_date(end) if end else None

    if end_obj:
        end_obj = end_obj.replace(hour=23, minute=59, second=59)

    # -----------------------------
    # PERIOD FILTER
    # -----------------------------
    def is_valid(t, mode="current"):
        date_obj = parse_date(t.get("created_at"))
        if not date_obj:
            return False

        ref_now = now

        # CURRENT PERIOD
        if mode == "current":

            if start_obj and end_obj:
                return start_obj.date() <= date_obj.date() <= end_obj.date()

            if start_obj and not end_obj:
                return date_obj.date() == start_obj.date()

            if view == "month":
                return date_obj.year == ref_now.year and date_obj.month == ref_now.month

            elif view == "week":
                start_week = ref_now - timedelta(days=ref_now.weekday())
                return date_obj.date() >= start_week.date()

            elif view == "day":
                return date_obj.date() == ref_now.date()

            return True

        # PREVIOUS PERIOD
        elif mode == "previous":

            if view == "month":
                prev_month = (ref_now.replace(day=1) - timedelta(days=1))
                return date_obj.year == prev_month.year and date_obj.month == prev_month.month

            elif view == "week":
                start_week = ref_now - timedelta(days=ref_now.weekday())
                last_week_start = start_week - timedelta(days=7)
                last_week_end = start_week - timedelta(days=1)
                return last_week_start.date() <= date_obj.date() <= last_week_end.date()

            elif view == "day":
                yesterday = ref_now - timedelta(days=1)
                return date_obj.date() == yesterday.date()

            return False

    def calculate(transactions, mode):
        revenue = 0
        count = 0

        for t in transactions:
            if not is_valid(t, mode):
                continue

            amount = float(t.get("total_net_billing") or 0)
            revenue += amount
            count += 1

        return revenue, count


    current_mainland_rev, current_mainland_tx = calculate(mainland_transactions, "current")
    current_floating_rev, current_floating_tx = calculate(floating_transactions, "current")

    prev_mainland_rev, prev_mainland_tx = calculate(mainland_transactions, "previous")
    prev_floating_rev, prev_floating_tx = calculate(floating_transactions, "previous")

    total_revenue = current_mainland_rev + current_floating_rev
    total_transactions = current_mainland_tx + current_floating_tx

    prev_total_revenue = prev_mainland_rev + prev_floating_rev
    prev_total_transactions = prev_mainland_tx + prev_floating_tx

    mainland_total = current_mainland_rev
    floating_total = current_floating_rev

    highest_name = "Mainland" if mainland_total >= floating_total else "Floating"
    highest_value = max(mainland_total, floating_total)

    avg_transaction_value = (
        total_revenue / total_transactions if total_transactions > 0 else 0
    )

    prev_avg_transaction_value = (
        prev_total_revenue / prev_total_transactions if prev_total_transactions > 0 else 0
    )


    def get_trend(current, previous):
        if previous == 0:
            return "+0%", True

        change = ((current - previous) / previous) * 100

        sign = "+" if change >= 0 else "-"
        return f"{sign}{abs(change):.1f}%", change >= 0

    revenue_trend, revenue_positive = get_trend(total_revenue, prev_total_revenue)
    tx_trend, tx_positive = get_trend(total_transactions, prev_total_transactions)
    aov_trend, aov_positive = get_trend(avg_transaction_value, prev_avg_transaction_value)

    return {
        "total_revenue": {
            "value": f"₱{total_revenue:,.2f}",
            "trend": revenue_trend,
            "positive": revenue_positive
        },
        "highest_performer": {
            "value": highest_name,
            "trend": f"₱{highest_value:,.2f}",
            "positive": True
        },
        "total_transactions": {
            "value": f"{total_transactions:,}",
            "trend": tx_trend,
            "positive": tx_positive
        },
        "avg_transaction_value": {
            "value": f"₱{avg_transaction_value:,.2f}",
            "trend": aov_trend,
            "positive": aov_positive
        }
    }


def get_revenue_base_tables():
    try:
        mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])
        floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

        streams = {
            "Mainland": {"txns": [], "color": "purple", "category": "Mainland Sales"},
            "Skydeck": {"txns": [], "color": "orange", "category": "Floating Bar"},
            "Maindeck": {"txns": [], "color": "green", "category": "Floating Bar"},
        }

        # MAINLAND
        for t in mainland_transactions:
            amount = float(t.get("total_net_billing") or 0)
            streams["Mainland"]["txns"].append(amount)

        # FLOATING
        for t in floating_transactions:
            amount = float(t.get("total_net_billing") or 0)
            deck = (t.get("deck_assigned") or "").lower().replace(" ", "")

            if deck == "skydeck":
                streams["Skydeck"]["txns"].append(amount)
            elif deck == "maindeck":
                streams["Maindeck"]["txns"].append(amount)

        table = []
        total_revenue = sum(sum(data["txns"]) for data in streams.values())

        for name, data in streams.items():
            revenue = sum(data["txns"])
            txn_count = len(data["txns"])
            avg = revenue / txn_count if txn_count > 0 else 0
            percent = (revenue / total_revenue * 100) if total_revenue > 0 else 0

            table.append({
                "stream": name,
                "icon": name[0],
                "category": data["category"],
                "cat_color": data["color"],
                "current": f"₱{revenue:,.0f}",
                "last": "N/A",
                "growth": "N/A",
                "percent": f"{percent:.1f}%",
                "txns": txn_count,
                "avg": f"₱{avg:,.2f}"
            })

        return table

    except Exception as e:
        print("Tables error:", e)
        return []
def get_revenue_base_tables():
    try:
        mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])
        floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

        streams = {
            "Mainland": {"txns": [], "color": "purple", "category": "Mainland Sales"},
            "Skydeck": {"txns": [], "color": "orange", "category": "Floating Bar"},
            "Maindeck": {"txns": [], "color": "green", "category": "Floating Bar"},
        }

        # -------------------------
        # MAINLAND
        # -------------------------
        for t in mainland_transactions:
            amount = float(t.get("total_net_billing") or 0)
            streams["Mainland"]["txns"].append(amount)

        # -------------------------
        # FLOATING (FIXED NORMALIZATION)
        # -------------------------
        for t in floating_transactions:
            amount = float(t.get("total_net_billing") or 0)

            deck = (t.get("deck_assigned") or "").lower().replace(" ", "")

            if deck == "skydeck":
                streams["Skydeck"]["txns"].append(amount)
            elif deck == "maindeck":
                streams["Maindeck"]["txns"].append(amount)

        # -------------------------
        # Compute totals
        # -------------------------
        table = []
        total_revenue = 0

        for data in streams.values():
            total_revenue += sum(data["txns"])

        # -------------------------
        # Build table
        # -------------------------
        for name, data in streams.items():
            revenue = sum(data["txns"])
            txn_count = len(data["txns"])
            avg = revenue / txn_count if txn_count > 0 else 0

            percent = (revenue / total_revenue * 100) if total_revenue > 0 else 0

            table.append({
                "stream": name,
                "icon": name[0],
                "category": data["category"],
                "cat_color": data["color"],
                "current": f"₱{revenue:,.0f}",
                "last": "N/A",
                "growth": "N/A",
                "percent": f"{percent:.1f}%",
                "txns": txn_count,
                "avg": f"₱{avg:,.2f}"
            })

        return table

    except Exception as e:
        print("Tables error:", e)
        return []
def get_revenue_base_totals():
    try:
        mainland_transactions = GLOBAL_DATA.get("mainland_transactions", [])
        floating_transactions = GLOBAL_DATA.get("floating_transactions", [])

        total_revenue = 0
        total_transactions = 0

        # Mainland
        for t in mainland_transactions:
            amount = float(t.get("total_net_billing") or 0)
            total_revenue += amount
            total_transactions += 1

        # Floating
        for t in floating_transactions:
            amount = float(t.get("total_net_billing") or 0)
            total_revenue += amount
            total_transactions += 1

        avg_transaction_value = (
            total_revenue / total_transactions if total_transactions > 0 else 0
        )

        return {
            "current": f"₱{total_revenue:,.0f}",
            "last": "N/A",
            "growth": "N/A",
            "percent": "100%",
            "txns": total_transactions,
            "avg": f"₱{avg_transaction_value:,.2f}"
        }

    except Exception as e:
        print("Totals error:", e)
        return {}
# Base data (Monthly)
BASE_REVENUE_DATA = {
    # "kpis": {
    #     "total_revenue": {"value": "₱507,000", "trend": "↗ +10.6%", "positive": True},
    #     "highest_performer": {"value": "Mainland", "trend": "↗ ₱285,000", "positive": True},
    #     "total_transactions": {"value": "6,375", "trend": "↗ +8.5%", "positive": True},
    #     "avg_transaction_value": {"value": "₱79.53", "trend": "↗ +2.0%", "positive": True}
    # },
    "kpis": get_kpis_base_revenue_data(),
    "charts": {
        # "distribution": {
        #     "labels": ["Mainland", "Skydeck", "Private Events", "Catering Services", "Gift Cards"],
        #     "data": [285000, 145000, 42000, 23000, 12000],
        #     "colors": ["#8b5cf6", "#f59e0b", "#10b981", "#ec4899", "#06b6d4"]
        # },
        "distribution": get_distribution_data(),
        # "trend_12_month": {
        #     "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        #     "datasets": [
        #         {"label": "Mainland", "data": [225000, 235000, 245000, 260000, 270000, 280000, 265000, 275000, 280000, 282000, 285000, 290000], "borderColor": "#8b5cf6", "backgroundColor": "transparent"},
        #         {"label": "Skydeck", "data": [115000, 120000, 125000, 130000, 140000, 142000, 135000, 142000, 145000, 145000, 146000, 148000], "borderColor": "#f59e0b", "backgroundColor": "transparent"},
        #         {"label": "Events", "data": [30000, 32000, 35000, 38000, 40000, 40000, 38000, 40000, 42000, 43000, 44000, 45000], "borderColor": "#10b981", "backgroundColor": "transparent"}
        #     ]
        # },
        "trend_12_month": get_combined_revenue_data(),
        # "last_7_days": {
        #     "labels": ["Mar 14", "Mar 15", "Mar 16", "Mar 17", "Mar 18", "Mar 19", "Mar 20"],
        #     "datasets": [
        #         {"label": "Mainland", "data": [9000, 11000, 9500, 12000, 10500, 13000, 11500], "backgroundColor": "#8b5cf6"},
        #         {"label": "Skydeck", "data": [4000, 5500, 5000, 6000, 5300, 7000, 6000], "backgroundColor": "#f59e0b"},
        #         {"label": "Events", "data": [1000, 1200, 1500, 1800, 1800, 2000, 1600], "backgroundColor": "#10b981"},
        #         {"label": "Catering", "data": [200, 400, 300, 500, 400, 600, 500], "backgroundColor": "#ec4899"},
        #         {"label": "Gift Cards", "data": [100, 150, 200, 250, 200, 300, 250], "backgroundColor": "#06b6d4"}
        #     ]
        # }
        "last_7_days": get_last_7_days_revenue(),
    },
    # "table": [
    #     {"stream": "Mainland", "icon": "M", "category": "Food Service", "cat_color": "purple", "current": 285000, "last": "₱265,000", "growth": "↗ +7.5%", "percent": "56.2%", "txns": 3420, "avg": "₱83.33"},
    #     {"stream": "Skydeck", "icon": "S", "category": "Beverage Service", "cat_color": "orange", "current": 145000, "last": "₱138,000", "growth": "↗ +5.1%", "percent": "28.6%", "txns": 2850, "avg": "₱50.88"},
    #     {"stream": "Private Events", "icon": "E", "category": "Event Service", "cat_color": "green", "current": 42000, "last": "₱35,000", "growth": "↗ +20.0%", "percent": "8.3%", "txns": 8, "avg": "₱5,250.00"},
    #     {"stream": "Catering Services", "icon": "C", "category": "Event Service", "cat_color": "green", "current": 23000, "last": "₱18,000", "growth": "↗ +27.8%", "percent": "4.5%", "txns": 12, "avg": "₱1,916.67"},
    #     {"stream": "Gift Cards & Vouchers", "icon": "G", "category": "Merchandise", "cat_color": "cyan", "current": 12000, "last": "₱10,500", "growth": "↗ +14.3%", "percent": "2.4%", "txns": 85, "avg": "₱141.18"}
    # ],
    "table": get_revenue_base_tables(),
    # "tables": get_table_base_revenue_data().get("table"),
    # "totals": {
    #     "current": 507000, "last": "₱466,500", "growth": "↗ +8.2%", "percent": "100%", "txns": 6375, "avg": "₱79.53"
    # }
    "totals": get_revenue_base_totals()
}



@app.route('/revenue-streams')
def revenue_streams():
    
    return render_template('revenue_streams.html')


def filter_transactions(transactions, view=None, start=None, end=None):
    now = datetime.now()
    filtered = []

    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    for t in transactions:
        date_obj = parse_date(t.get("created_at"))
        if not date_obj:
            continue


        if start_date and end_date:
            if start_date.date() <= date_obj.date() <= end_date.date():
                filtered.append(t)
            continue


        if start_date and not end_date:
            if date_obj.date() == start_date.date():
                filtered.append(t)
            continue

        if view == "month":
            if date_obj.year == now.year and date_obj.month == now.month:
                filtered.append(t)

        elif view == "week":
            if date_obj >= now - timedelta(days=7):
                filtered.append(t)

        elif view == "day":
            if date_obj.date() == now.date():
                filtered.append(t)

        else:
            filtered.append(t)

    return filtered
@app.route('/api/revenue-streams')
def get_revenue_data():

    view = request.args.get('view', 'month')
    start = request.args.get('start')
    end = request.args.get('end')

    return jsonify({
        "kpis": get_kpis_base_revenue_data(view, start, end),
        "charts": {
            "distribution": get_distribution_data(view, start, end),
            "trend_12_month": get_combined_revenue_data(),
            "last_7_days": get_last_7_days_revenue(),
        },
        "table": get_revenue_base_tables(),
        "totals": get_revenue_base_totals()
    })

# --------------------------------------------


#             5.) CASH OPERATIONS


# --------------------------------------------

@app.route('/api/reconcile-drawer', methods=['PUT'])
def reconcile_drawer():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400

        result = put_employee_drawer_reconcile(data)

        # handle errors from function
        if result.get("status") == "error":
            return jsonify(result), 400

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def cash_operation_data_transaction():

    try:
        mainland = GLOBAL_DATA.get("mainland_transactions", [])
        floating = GLOBAL_DATA.get("floating_transactions", [])

        # ----------------------------
        # SAFE TYPE CHECK
        # ----------------------------
        if not isinstance(mainland, list):
            mainland = []

        if not isinstance(floating, list):
            floating = []

        combined = []

        # ----------------------------
        # SAFE DATE PARSER
        # ----------------------------
        def parse_datetime_safe(date_val):
            if isinstance(date_val, datetime):
                return date_val

            if not date_val:
                return None

            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%a, %d %b %Y %H:%M:%S %Z"
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_val, fmt)
                except:
                    continue

            return None

        # ----------------------------
        # MAINLAND (FIXED FILTER)
        # ----------------------------
        for t in mainland:

        
            if not t.get("total_net_billing"):
                continue

            dt = parse_datetime_safe(t.get("created_at"))
            if not dt:
                continue

            combined.append({
                "timestamp": dt,
                "register": "Mainland",
                "type": t.get("mode_of_payment") or "N/A",
                "reference": t.get("transaction_id"),
                "amount": float(t.get("total_net_billing") or 0),
                "cashier": t.get("attended_by") or "N/A",
                "notes": t.get("notes") or "N/A",
            })

        # ----------------------------
        # FLOATING BAR
        # ----------------------------
        for t in floating:

            if not t.get("total_net_billing"):
                continue

            dt = parse_datetime_safe(t.get("created_at"))
            if not dt:
                continue

            combined.append({
                "timestamp": dt,
                "register": "Floating Bar",
                "type": t.get("mode_of_payment") or "N/A",
                "reference": t.get("transaction_id"),
                "amount": float(t.get("total_net_billing") or 0),
                "cashier": t.get("attended_by") or "N/A",
                "notes": t.get("notes") or "N/A",
            })

        # ----------------------------
        # SORT + LIMIT (LAST 50)
        # ----------------------------
        combined.sort(key=lambda x: x["timestamp"], reverse=True)
        last_50 = combined[:50]

        # ----------------------------
        # FORMAT OUTPUT
        # ----------------------------
        result = []

        for t in last_50:
            result.append({
                "timestamp": t["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "register": t["register"],
                "type": t["type"],
                "reference": t["reference"],
                "amount": f"₱{t['amount']:,.2f}",
                "cashier": t["cashier"],
                "notes": t["notes"]
            })

        return result

    except Exception as e:
        print("TRANSACTION ERROR:", str(e))
        return []
def get_registers_summary():
    try:
        data = GLOBAL_DATA.get("drawer", [])

        if not isinstance(data, list):
            return []

        result = []

        for row in data:

            # ----------------------------
            # ONLY ACTIVE RECORDS
            # ----------------------------
            if (row.get("status") or "").lower() != "active":
                continue

            balance = float(row.get("current_balance") or 0)

            result.append({
                "id": row.get("drawer_id"),          
                "name": row.get("register"),           
                "location": row.get("assigned_to"),    
                "balance": f"₱{balance:,.2f}",
                "status": row.get("status")
            })

        return result

    except Exception as e:
        print("REGISTER ERROR:", str(e))
        return []

def get_cash_kpis():
    try:
        data = GLOBAL_DATA.get("drawer", [])

        if not isinstance(data, list):
            return {}

        total_starting_cash = 0
        total_sales = 0
        total_safe_deposit = 0
        total_current_balance = 0

        for row in data:
            # if (row.get("status") or "").lower() != "active":
            #     continue
            total_starting_cash += float(row.get("starting_cash") or 0)
            total_sales += float(row.get("total_sales") or 0)
            total_safe_deposit += float(row.get("safe_deposit") or 0)
            total_current_balance += float(row.get("current_balance") or 0)

        return {
            "cash_on_hand": {
                "value": f"₱{total_starting_cash:,.2f}",
                "trend": ""
            },
            "cash_sales": {
                "value": f"₱{total_sales:,.2f}",
                "trend": ""
            },
            "safe_deposits": {
                "value": f"₱{total_safe_deposit:,.2f}",
                "trend": ""
            },
            "in_registers": {
                "value": f"₱{total_current_balance:,.2f}",
                "trend": ""
            }
        }

    except Exception as e:
        print("KPI ERROR:", str(e))
        return {
            "cash_on_hand": {"value": "₱0.00", "trend": ""},
            "cash_sales": {"value": "₱0.00", "trend": ""},
            "safe_deposits": {"value": "₱0.00", "trend": ""},
            "in_registers": {"value": "₱0.00", "trend": ""}
        }

    
CASH_OPERATIONS_DATA = {
    # "kpis": {
    #     "cash_on_hand": {"value": "₱53,770.50", "trend": "↗ +12.5%", "positive": True},
    #     "cash_sales": {"value": "₱7,830.00", "trend": "↗ Today", "positive": True},
    #     "safe_deposits": {"value": "₱16,000.00", "trend": "🕒 Secure", "positive": True},
    #     "in_registers": {"value": "₱37,770.50", "trend": "🕒 In Registers", "positive": True}
    # },
    "kpis" : get_cash_kpis(),
    # "registers": [
    #     {"id": "REG-001", "name": "Mainland - Main Counter", "location": "Mainland", "balance": "₱15,420.50", "status": "active"},
    #     {"id": "REG-002", "name": "Floating Bar- Bar", "location": "Skydeck", "balance": "₱22,350.00", "status": "active"}
    # ],
    "registers": get_registers_summary(),
    # "transactions": [
    #     {"timestamp": "2026-03-20 14:35:00", "register": "Mainland - Main Counter", "reg_id": "REG-001", "type": "Cash Sale", "type_color": "green", "reference": "ORD-2451", "amount": "+₱1,250.00", "amount_color": "text-green-600", "balance": "₱15,420.50", "cashier": "Lucille Marfa", "notes": "Table 12 - Cash payment"},
    #     {"timestamp": "2026-03-20 14:20:00", "register": "Floating Bar- Bar", "reg_id": "REG-002", "type": "Safe Drop", "type_color": "red", "reference": "SD-089", "amount": "-₱5,000.00", "amount_color": "text-red-600", "balance": "₱22,350.00", "cashier": "Juan Dela Cruz", "notes": "Regular safe deposit"},
    #     {"timestamp": "2026-03-20 14:10:00", "register": "Mainland - Main Counter", "reg_id": "REG-001", "type": "Cash Sale", "type_color": "green", "reference": "ORD-2450", "amount": "+₱850.00", "amount_color": "text-green-600", "balance": "₱14,170.50", "cashier": "Jarek Melgar", "notes": "Table 8 - Cash payment"},
    #     {"timestamp": "2026-03-20 13:55:00", "register": "Floating Bar- Bar", "reg_id": "REG-002", "type": "Petty Cash", "type_color": "blue", "reference": "PC-034", "amount": "+₱500.00", "amount_color": "text-green-600", "balance": "₱22,850.00", "cashier": "Vlad Navarro", "notes": "Petty cash replenishment"},
    #     {"timestamp": "2026-03-20 13:40:00", "register": "Floating Bar- Bar", "reg_id": "REG-002", "type": "Cash Sale", "type_color": "green", "reference": "ORD-2449", "amount": "+₱3,200.00", "amount_color": "text-green-600", "balance": "₱26,350.00", "cashier": "Jarek Melgar", "notes": "Group order - Cash payment"},
    #     {"timestamp": "2026-03-20 13:25:00", "register": "Mainland - Main Counter", "reg_id": "REG-001", "type": "Refund", "type_color": "red", "reference": "REF-078", "amount": "-₱320.00", "amount_color": "text-red-600", "balance": "₱13,320.50", "cashier": "Lucille Marfa", "notes": "Customer refund - Order cancellation"},
    #     {"timestamp": "2026-03-20 13:10:00", "register": "Floating Bar- Bar", "reg_id": "REG-002", "type": "Cash Sale", "type_color": "green", "reference": "ORD-2448", "amount": "+₱680.00", "amount_color": "text-green-600", "balance": "₱25,670.00", "cashier": "Vlad Navarro", "notes": "Takeout order - Cash payment"},
    #     {"timestamp": "2026-03-20 12:50:00", "register": "Floating Bar- Bar", "reg_id": "REG-002", "type": "Cash Sale", "type_color": "green", "reference": "ORD-2447", "amount": "+₱1,850.00", "amount_color": "text-green-600", "balance": "₱24,150.00", "cashier": "Jarek Melgar", "notes": "Bar orders - Cash payment"}
    # ]
    "transactions": cash_operation_data_transaction()
}
@app.route('/drawer/update-current-balance', methods=['PUT'])
def update_employee_drawer_current_balance_cash_operation():
    try:
        data = request.get_json()

        cash_result = post_cash_in_out(data)
        result = put_employee_drawer_cash_current_balance(data)

        if cash_result.get("status") == "error":
            return jsonify(cash_result), 400

        if result.get("status") == "error":
            return jsonify(result), 400

        return jsonify({
            "drawer": result,
            "cash": cash_result
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/drawer/update-safe-deposit', methods=['PUT'])
def update_employee_drawer_safe_deposit():
    try:
        data = request.get_json()

        result = put_employee_drawer_safe_register(data)

        if result.get("status") == "error":
            return jsonify(result), 400

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/employee-drawer/active', methods=['GET'])
def get_active_employee_drawer_history_route():
    try:
        result = get_active_employee_drawer_history()


        if isinstance(result, dict) and result.get("status") == "error":
            return jsonify(result), 400

        return jsonify({
            "status": "success",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cash-operations')
def cash_operations():
    data = get_register()
    active_drawer = get_active_employee_drawer_history()

    return render_template('cash_operations.html', register = data, active_drawer = active_drawer)

@app.route('/api/cash-operations')
def get_cash_operations_data():
    try:
        data = {
            "kpis": get_cash_kpis(),
            "registers": get_registers_summary(),
            "transactions": cash_operation_data_transaction()
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ---------------------------------------------

#             DRAWER ASSIGNMENT

# ----------------------------------------------
@app.route("/employee-drawer/add-register", methods = ["POST"])
def post_register_route():
    try:
        data = request.get_json()
        result = post_register(data)
        # employee_update = put_mainland_employee_by_id

        if result.get("status") == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        

    except Exception as e:
        return {"status": "error", "message" : str(e)}

@app.route("/employee-drawer/<int:id>", methods=["PUT"])
def update_employee_drawer(id):
    try:
        data = request.get_json()

        result = put_employee_drawer_history(id, data)

        if result.get("status") == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/employee-drawer/transfer/<int:id>", methods=["PUT"])
def transfer_drawer(id):
    try:
        data = request.get_json()
        new_cashier = data.get("cashier")

        if not new_cashier:
            return jsonify({
                "status": "error",
                "message": "Cashier is required"
            }), 400

        result = transfer_drawer_cashier(id, new_cashier)

        if result.get("status") == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@app.route("/employee-drawer", methods= ["POST"])
def post_employe_drawer():
    try:
        data = request.get_json()
        result = post_employee_drawer_history(data)

        if result.get("status") == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
def get_mainland_kpis_drawer_assignment():
    try:
      
        drawers = GLOBAL_DATA.get("drawer", [])
        if not drawers or isinstance(drawers, dict):
            drawers = []

        active_drawers_count = 0
        total_cash = 0
        total_sales = 0

        for d in drawers:
            if d.get("status") == "Active" and d.get("assigned_to").lower() == "mainland":
                active_drawers_count += 1
                total_cash += float(d.get("current_balance") or 0)
                total_sales += float(d.get("total_sales") or 0)

        transactions = get_mainland_transaction()
        if not transactions or isinstance(transactions, dict):
            transactions = []

        today = datetime.now().date()
        total_transactions = 0

        for txn in transactions:
            created_at = txn.get("created_at")
            attended_by = txn.get("attended_by")

            if not created_at:
                continue

            # ensure datetime
            if isinstance(created_at, str):
                created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")

            # same day only
            if created_at.date() != today:
                continue

            # ignore invalid attendants
            if not attended_by or attended_by == "N/A":
                continue

            total_transactions += 1

        return {
            "active_drawers": str(active_drawers_count),
            "total_cash": f"₱{total_cash:,.2f}",
            "total_sales": f"₱{total_sales:,.2f}",
            "total_transactions": str(total_transactions)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def get_active_drawer_mainland_assignment():
    try:
        rows = GLOBAL_DATA.get("drawer", "")
        transactions = GLOBAL_DATA.get("mainland_transactions", [])

        if not rows or isinstance(rows, dict):
            rows = []

        if not transactions or isinstance(transactions, dict):
            transactions = []

        active_drawers = []

        for row in rows:

            if (
                (row.get("status") or "").lower() != "active"
                or (row.get("assigned_to") or "").lower() != "mainland"
            ):
                continue

            starting_cash = float(row.get("starting_cash") or 0)
            total_sales = float(row.get("total_sales") or 0)
            current_balance = float(row.get("current_balance") or starting_cash)

            cashier_name = row.get("cashier")
            start_time = row.get("start_time")

            if isinstance(start_time, str):
                try:
                    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                except:
                    start_time = None

            transaction_count = 0

            if start_time:
                start_date = start_time.date()

                for txn in transactions:
                    txn_attended_by = txn.get("attended_by")
                    txn_type = txn.get("type_of_transaction")

                    created_at = txn.get("created_at")

                    if not created_at:
                        continue

                    # ensure datetime
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                        except:
                            continue

                    if created_at.date() != start_date:
                        continue

                    # match cashier name
                    if txn_attended_by == cashier_name or txn_type == cashier_name:
                        transaction_count += 1

            active_drawers.append({
                "id": row.get("id"), 
                "drawer_id": row.get("drawer_id"),
                "register": row.get("register"),
                "reg_id": None,
                "cashier": cashier_name,
                "cashier_id": None,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else None,

                "current_balance": f"₱{current_balance:,.2f}",
                "raw_expected": current_balance,

                "total_sales": f"₱{total_sales:,.2f}",
                "starting_float": f"₱{starting_cash:,.2f}",

                "transactions": transaction_count, 

                "status": "Active"
            })

        return active_drawers

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
def get_closed_drawer_mainland_assignment():
    try:
        rows = GLOBAL_DATA.get("drawer", [])

        if not rows or isinstance(rows, dict):
            rows = []

        history = []

        for row in rows:

            if (
                (row.get("status") or "").lower() != "closed"
                or (row.get("assigned_to") or "").lower() != "mainland"
            ):
                continue

            variance_value = float(row.get("cash_variance") or 0)

            history.append({
                "drawer_id": row.get("drawer_id"),
                "register": row.get("register"),
                "reg_id": None,
                "cashier": row.get("cashier"),
                "cashier_id": None,
                "start_time": row.get("start_time").strftime("%Y-%m-%d %H:%M:%S") if row.get("start_time") else None,
                "end_time": row.get("end_time").strftime("%Y-%m-%d %H:%M:%S") if row.get("end_time") else None,
                "starting_float": f"₱{float(row.get('starting_cash') or 0):,.2f}",
                "total_sales": f"₱{float(row.get('total_sales') or 0):,.2f}",
                "ending_balance": f"₱{float(row.get('ending_balance') or 0):,.2f}",
                "variance": f"₱{variance_value:,.2f}",
                "variance_color": "text-green-600" if variance_value >= 0 else "text-red-600",
                "status": row.get("status")
            })

        return history

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
def get_floatingbar_kpis_drawer_assignment():
    try:
        drawers = GLOBAL_DATA.get("drawer", [])
        if not drawers or isinstance(drawers, dict):
            drawers = []

        transactions = GLOBAL_DATA.get("floating_transactions", [])
        if not transactions or isinstance(transactions, dict):
            transactions = []

        active_drawers_count = 0
        total_cash = 0
        total_sales = 0
        total_transactions = 0

        today = datetime.now().date()

        for d in drawers:
            status = (d.get("status") or "").lower()
            assigned_to = (d.get("assigned_to") or "").replace(" ", "").lower()

            if status == "active" and assigned_to == "floatingbar":
                active_drawers_count += 1
                total_cash += float(d.get("current_balance") or 0)
                total_sales += float(d.get("total_sales") or 0)

        for txn in transactions:
            created_at = txn.get("created_at")
            attended_by = txn.get("attended_by")

            if not created_at:
                continue

            # parse datetime
            date_obj = None

            if isinstance(created_at, str):
                try:
                    date_obj = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        date_obj = datetime.strptime(created_at, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        continue
            else:
                date_obj = created_at

            if not date_obj:
                continue

            # filter today
            if date_obj.date() != today:
                continue

            if not attended_by or attended_by == "N/A":
                continue

            total_transactions += 1

        return {
            "active_drawers": str(active_drawers_count),
            "total_cash": f"₱{total_cash:,.2f}",
            "total_sales": f"₱{total_sales:,.2f}",
            "total_transactions": str(total_transactions)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    

def get_active_drawer_floatingbar_assignment():
    try:
        rows = GLOBAL_DATA.get("drawer", [])
        transactions = GLOBAL_DATA.get("floating_transactions", [])

        if not rows or isinstance(rows, dict):
            rows = []

        if not transactions or isinstance(transactions, dict):
            transactions = []

        active_drawers = []

        for row in rows:


            if (
                (row.get("status") or "").lower() != "active"
                or (row.get("assigned_to") or "").replace(" ", "").lower() != "floatingbar"
            ):
                continue

            starting_cash = float(row.get("starting_cash") or 0)
            total_sales = float(row.get("total_sales") or 0)
            current_balance = float(row.get("current_balance") or starting_cash)

            cashier_name = row.get("cashier")
            start_time = row.get("start_time")


            if isinstance(start_time, str):
                try:
                    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                except:
                    start_time = None

            transaction_count = 0

            if start_time:
                start_date = start_time.date()

                for txn in transactions:
                    txn_attended_by = txn.get("attended_by")
                    txn_type = txn.get("type_of_transaction")

                    created_at = txn.get("created_at")

                    if not created_at:
                        continue

                    # same datetime handling style
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                        except:
                            try:
                                created_at = datetime.strptime(created_at, "%a, %d %b %Y %H:%M:%S %Z")
                            except:
                                continue

                    # same day check
                    if created_at.date() != start_date:
                        continue

                    # match cashier
                    if txn_attended_by == cashier_name or txn_type == cashier_name:
                        transaction_count += 1

            active_drawers.append({
                "id": row.get("id"), 
                "drawer_id": row.get("drawer_id"),
                "register": row.get("register"),
                "reg_id": None,
                "cashier": cashier_name,
                "cashier_id": None,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else None,

                "current_balance": f"₱{current_balance:,.2f}",
                "raw_expected": current_balance,

                "total_sales": f"₱{total_sales:,.2f}",
                "starting_float": f"₱{starting_cash:,.2f}",

                "transactions": transaction_count, 

                "status": "Active"
            })

        
  

        return active_drawers

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
def get_closed_drawer_floatingbar_assignment():
    try:
        rows = GLOBAL_DATA.get("drawer", [])

        if not rows or isinstance(rows, dict):
            rows = []

        history = []

        for row in rows:
            if (
                (row.get("status") or "").lower() != "closed"
                or (row.get("assigned_to") or "").replace(" ", "").lower() != "floatingbar"
            ):
                continue

            variance_value = float(row.get("cash_variance") or 0)

            start_time = row.get("start_time")
            end_time = row.get("end_time")


            if isinstance(start_time, str):
                try:
                    start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                except:
                    start_time = None

            if isinstance(end_time, str):
                try:
                    end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                except:
                    end_time = None

            history.append({
                "drawer_id": row.get("drawer_id"),
                "register": row.get("register"),
                "reg_id": None,
                "cashier": row.get("cashier"),
                "cashier_id": None,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else None,
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else None,
                "starting_float": f"₱{float(row.get('starting_cash') or 0):,.2f}",
                "total_sales": f"₱{float(row.get('total_sales') or 0):,.2f}",
                "ending_balance": f"₱{float(row.get('ending_balance') or 0):,.2f}",
                "variance": f"₱{variance_value:,.2f}",
                "variance_color": "text-green-600" if variance_value >= 0 else "text-red-600",
                "status": row.get("status")
            })

        return history

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.route("/employee-drawer/history", methods=["POST"])
def add_employee_drawer_history():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No input data provided"
            }), 400

        required_fields = ["drawer_id", "register", "cashier", "start_time"]

        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "status": "error",
                    "message": f"{field} is required"
                }), 400


        result = post_employee_drawer_history(data)

        if result.get("status") == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500   



DRAWER_ASSIGNMENT_DATA = {
    "locations": {
        "mainland": {
            # "kpis": {
            #     "active_drawers": "1",
            #     "total_cash": "₱15,420.50",
            #     "total_sales": "₱12,850.00",
            #     "total_transactions": "47"
            # },
            "kpis": get_mainland_kpis_drawer_assignment(),
            # "active_drawers": [
            #     {
            #         "drawer_id": "DRW-001",
            #         "register": "Mainland - Main Counter",
            #         "reg_id": "REG-001",
            #         "cashier": "Lucille Marfa",
            #         "cashier_id": "CSH-001",
            #         "start_time": "2026-03-20 08:00:00",
            #         "current_balance": "₱15,420.50",
            #         "raw_expected": 15420.50,
            #         "total_sales": "₱12,850.00",
            #         "starting_float": "₱5,000.00",
            #         "transactions": 47,
            #         "status": "Active"
            #     }
            # ],
            "active_drawers": get_active_drawer_mainland_assignment(),
            # "history": [
            #     {
            #         "drawer_id": "DRW-H-001",
            #         "register": "Mainland - Main Counter",
            #         "reg_id": "REG-001",
            #         "cashier": "Vlad Navarro",
            #         "cashier_id": "CSH-003",
            #         "start_time": "2026-03-19 14:00:00",
            #         "end_time": "2026-03-19 22:00:00",
            #         "starting_float": "₱5,000.00",
            #         "total_sales": "₱15,250.00",
            #         "ending_balance": "₱18,450.00",
            #         "variance": "₱0.00",
            #         "variance_color": "text-green-600",
            #         "status": "closed"
            #     }
            # ]
            "history": get_closed_drawer_mainland_assignment()
        },
        "floatingbar": {
            # "kpis": {
            #     "active_drawers": "1",
            #     "total_cash": "₱22,350.00",
            #     "total_sales": "₱18,350.00",
            #     "total_transactions": "63"
            # },
            "kpis": get_floatingbar_kpis_drawer_assignment(),
            # "active_drawers": [
            #     {
            #         "drawer_id": "DRW-002",
            #         "register": "Floating - Bar",
            #         "reg_id": "REG-002",
            #         "cashier": "Jarek Melgar",
            #         "cashier_id": "CSH-002",
            #         "start_time": "2026-03-20 09:00:00",
            #         "current_balance": "₱22,350.00",
            #         "raw_expected": 22350.00,
            #         "total_sales": "₱18,350.00",
            #         "starting_float": "₱4,000.00",
            #         "transactions": 63,
            #         "status": "Active"
            #     }
            # ],
            "active_drawers": get_active_drawer_floatingbar_assignment(),
            # "history": [
            #     {
            #         "drawer_id": "DRW-H-002",
            #         "register": "Floating - Bar",
            #         "reg_id": "REG-002",
            #         "cashier": "Dylan Ray Cairo",
            #         "cashier_id": "CSH-004",
            #         "start_time": "2026-03-19 08:00:00",
            #         "end_time": "2026-03-19 16:00:00",
            #         "starting_float": "₱3,000.00",
            #         "total_sales": "₱11,850.00",
            #         "ending_balance": "₱14,200.00",
            #         "variance": "-₱50.00",
            #         "variance_color": "text-red-600",
            #         "status": "closed"
            #     }
            # ]
            "history" : get_closed_drawer_floatingbar_assignment()
        },


    }
}




@app.route('/drawer-assignment')
def drawer_assignment():
    try:
        register = get_register()

        cashier_mainland = get_mainland_employee()

        cashier_floating_response = requests.get(FLOATING_API_URL_EMPLOYEES)
        cashier_floating = cashier_floating_response.json()

        cashiers = cashier_mainland + cashier_floating



        return render_template('drawer_assignment.html', register=register, cashier = cashiers)

    except Exception as e:
        return str(e), 500

@app.route('/api/drawer-assignment')
def get_drawer_assignment_data():
    return jsonify({
        "locations": {
            "mainland": {
                "kpis": get_mainland_kpis_drawer_assignment(),
                "active_drawers": get_active_drawer_mainland_assignment(),
                "history": get_closed_drawer_mainland_assignment()
            },
            "floatingbar": {
                "kpis": get_floatingbar_kpis_drawer_assignment(),
                "active_drawers": get_active_drawer_floatingbar_assignment(),
                "history": get_closed_drawer_floatingbar_assignment()
            }
        }
    })
# ---------------------------------------------------


#                     6.) SHIFT LOGS

# -------------- -------------------------------------
def get_today_employee_shifts_mainland():
    try:
        rows = GLOBAL_DATA.get("drawer", [])

        if not rows or isinstance(rows, dict):
            rows = []

        shifts = []
        shift_counter = 1

        today = datetime.now().date()

        for row in rows:
            start_time = row.get("start_time")

            if not start_time:
                continue

           
            if isinstance(start_time, str):
                start_time_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            else:
                start_time_obj = start_time

        
            if start_time_obj.date() != today:
                continue

            end_time = row.get("end_time")

         
            if end_time:
                if isinstance(end_time, str):
                    end_time_str = end_time
                else:
                    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_time_str = "In Progress"

            variance_value = float(row.get("cash_variance") or 0)

            shifts.append({
                "shift_id": f"SFT-{shift_counter:03d}",  
                "cashier_name": row.get("cashier"),
                "cashier_id": row.get("cashier_id"),
                "register_name": row.get("register"),
                "register_loc": "Mainland",
                "start_time": start_time_obj.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time_str,
                "sales": f"₱{float(row.get('total_sales') or 0):,.2f}",
                "transactions": row.get("transactions") or 0,
                "variance": f"₱{variance_value:,.2f}" if end_time else "—",
                "variance_color": "text-green-600" if variance_value >= 0 else "text-red-600",
                "status": row.get("status")
            })

            shift_counter += 1

        return shifts

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
def get_today_kpis_shift_log():
    try:
        drawers = GLOBAL_DATA.get("drawer", [])
        transactions = GLOBAL_DATA.get("mainland_transactions", [])

        if not drawers or isinstance(drawers, dict):
            drawers = []

        if not transactions or isinstance(transactions, dict):
            transactions = []

        today = datetime.now().date()

        # ----------------------------
        # ACTIVE CASHIERS
        # ----------------------------
        active_cashiers = set()

        for d in drawers:
            status = (d.get("status") or "").strip().lower()
            assigned_to = (d.get("assigned_to") or "").strip().lower()

            if status == "active" and assigned_to == "mainland":
                cashier_name = (d.get("cashier") or "").strip()
                if cashier_name:
                    active_cashiers.add(cashier_name)

        # ----------------------------
        # TRANSACTIONS KPI
        # ----------------------------
        total_sales = 0.0
        total_transactions = 0

        for t in transactions:
            txn_type = (t.get("type_of_transaction") or "").lower()

            # Get correct date field
            if txn_type == "reservation":
                txn_date_val = t.get("reservation_datetime") or t.get("created_at")
            else:
                txn_date_val = t.get("created_at")

            if not txn_date_val:
                continue

            # Parse datetime
            if isinstance(txn_date_val, datetime):
                txn_datetime = txn_date_val
            else:
                try:
                    txn_datetime = datetime.strptime(txn_date_val, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        txn_datetime = datetime.strptime(txn_date_val, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        continue

            if not txn_datetime:
                continue

            # Filter today
            if txn_datetime.date() != today:
                continue

            # Status filter
            status = (t.get("status") or "").lower()
            if status not in ["confirmed", "billout"]:
                continue

            # Amount
            try:
                amount = float(t.get("total_net_billing") or 0)
            except:
                amount = 0

            total_sales += amount
            total_transactions += 1

        avg_transaction = (
            total_sales / total_transactions if total_transactions > 0 else 0
        )

        return {
            "active_cashiers": len(active_cashiers),
            "total_sales_today": f"₱{total_sales:,.2f}",
            "total_transactions": str(total_transactions),
            "avg_transaction": f"₱{avg_transaction:,.3f}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def get_today_employee_shifts_floatingbar():
    try:
        rows = GLOBAL_DATA.get("drawer")

        if not rows or isinstance(rows, dict):
            rows = []

        shifts = []
        shift_counter = 1

        today = datetime.now().date()

        for row in rows:
            start_time = row.get("start_time")

            if not start_time:
                continue

            # parse start_time
            if isinstance(start_time, str):
                try:
                    start_time_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                except:
                    continue
            else:
                start_time_obj = start_time

            # filter today
            if start_time_obj.date() != today:
                continue

            # filter floatingbar
            assigned_to = (row.get("assigned_to") or "").replace(" ", "").lower()
            if assigned_to != "floatingbar":
                continue

            # end_time handling
            end_time = row.get("end_time")

            if end_time:
                if isinstance(end_time, str):
                    end_time_str = end_time
                else:
                    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_time_str = "In Progress"

            variance_value = float(row.get("cash_variance") or 0)

            shifts.append({
                "shift_id": f"SFT-{shift_counter:03d}",
                "cashier_name": row.get("cashier"),
                "cashier_id": row.get("cashier_id"),
                "register_name": row.get("register"),
                "register_loc": "Floating Bar",
                "start_time": start_time_obj.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time_str,
                "sales": f"₱{float(row.get('total_sales') or 0):,.2f}",
                "transactions": row.get("transactions") or 0,
                "variance": f"₱{variance_value:,.2f}" if end_time else "—",
                "variance_color": "text-green-600" if variance_value >= 0 else "text-red-600",
                "status": row.get("status")
            })

            shift_counter += 1

        return shifts

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
   
def get_today_kpis_shift_log_floatingbar():
    try:
        drawers = GLOBAL_DATA.get("drawer", [])
        transactions = GLOBAL_DATA.get("floating_transactions", [])

        if not drawers or isinstance(drawers, dict):
            drawers = []

        if not transactions or isinstance(transactions, dict):
            transactions = []

        today = datetime.now().date()

        # ----------------------------
        # ACTIVE CASHIERS (Floating Bar)
        # ----------------------------
        active_cashiers = set()

        for d in drawers:
            status = (d.get("status") or "").strip().lower()
            assigned_to = (d.get("assigned_to") or "").strip().lower()

            if status == "active" and assigned_to == "floating bar":
                cashier_name = (d.get("cashier") or "").strip()
                if cashier_name:
                    active_cashiers.add(cashier_name)

        # ----------------------------
        # TRANSACTIONS KPI (Floating Bar)
        # ----------------------------
        total_sales = 0.0
        total_transactions = 0

        for t in transactions:
            txn_type = (t.get("type_of_transaction") or "").lower()

            # choose correct date field
            if txn_type == "reservation":
                txn_date_val = t.get("reservation_datetime") or t.get("created_at")
            else:
                txn_date_val = t.get("created_at")

            if not txn_date_val:
                continue

            # parse datetime
            txn_datetime = None

            if isinstance(txn_date_val, datetime):
                txn_datetime = txn_date_val
            else:
                try:
                    txn_datetime = datetime.strptime(txn_date_val, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        txn_datetime = datetime.strptime(txn_date_val, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        continue

            if not txn_datetime:
                continue

            # filter today
            if txn_datetime.date() != today:
                continue

            # status filter
            status = (t.get("status") or "").lower()
            if status not in ["confirmed", "billout"]:
                continue

            # amount
            try:
                amount = float(t.get("total_net_billing") or 0)
            except:
                amount = 0

            total_sales += amount
            total_transactions += 1

        avg_transaction = (
            total_sales / total_transactions if total_transactions > 0 else 0
        )

        return {
            "active_cashiers": len(active_cashiers),
            "total_sales_today": f"₱{total_sales:,.2f}",
            "total_transactions": str(total_transactions),
            "avg_transaction": f"₱{avg_transaction:,.3f}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.route('/drawer/end-shift', methods=['PUT'])
def end_drawer_shift():
    try:
        data = request.get_json()

        result = end_employee_drawer_history_shift(data)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
SHIFT_LOGS_DATA = {
    "locations": {
        "mainland": {
            # "kpis": {
            #     "active_cashiers": "1",
            #     "total_sales_today": "₱48,750.50",
            #     "total_transactions": "127",
            #     "avg_transaction": "₱383.862"
            # },
            "kpis": get_today_kpis_shift_log(),
            # "shifts": [
            #     {
            #         "shift_id": "SFT-001",
            #         "cashier_name": "Lucille Marfa",
            #         "cashier_id": "CSH-001",
            #         "register_name": "Mainland - Main Counter",
            #         "register_loc": "Mainland",
            #         "start_time": "2026-03-20 08:00:00",
            #         "end_time": "In Progress",
            #         "sales": "₱48,750.50",
            #         "transactions": 127,
            #         "variance": "—",
            #         "variance_color": "text-gray-400",
            #         "status": "Active"
            #     },
            #     {
            #         "shift_id": "SFT-003",
            #         "cashier_name": "Jarek Melgar",
            #         "cashier_id": "CSH-002",
            #         "register_name": "Mainland - Main Counter",
            #         "register_loc": "Mainland",
            #         "start_time": "2026-03-19 08:00:00",
            #         "end_time": "2026-03-19 17:00:00",
            #         "sales": "₱72,450.25",
            #         "transactions": 198,
            #         "variance": "—",
            #         "variance_color": "text-gray-400",
            #         "status": "Completed"
            #     }
            # ]
            "shifts": get_today_employee_shifts_mainland()
        },
        "floatingbar": {
            # "kpis": {
            #     "active_cashiers": "1",
            #     "total_sales_today": "₱35,200.00",
            #     "total_transactions": "89",
            #     "avg_transaction": "₱395.506"
            # },

            "kpis": get_today_kpis_shift_log_floatingbar(),
            # "shifts": [
            #     {
            #         "shift_id": "SFT-002",
            #         "cashier_name": "Vlad Navarro",
            #         "cashier_id": "CSH-003",
            #         "register_name": "Floating Bar- Bar",
            #         "register_loc": "Skydeck",
            #         "start_time": "2026-03-20 08:00:00",
            #         "end_time": "In Progress",
            #         "sales": "₱35,200.00",
            #         "transactions": 89,
            #         "variance": "—",
            #         "variance_color": "text-gray-400",
            #         "status": "Active"
            #     },
            #     {
            #         "shift_id": "SFT-004",
            #         "cashier_name": "Dylan Ray Cairo",
            #         "cashier_id": "CSH-004",
            #         "register_name": "Floating Bar- Bar",
            #         "register_loc": "Skydeck",
            #         "start_time": "2026-03-19 08:00:00",
            #         "end_time": "2026-03-19 17:00:00",
            #         "sales": "₱45,890.75",
            #         "transactions": 134,
            #         "variance": "₱50.00",
            #         "variance_color": "text-red-600 font-medium",
            #         "status": "Completed"
            #     }
            # ]
            "shifts": get_today_employee_shifts_floatingbar()
        }
    }
}

@app.route('/shift-logs')
def shift_logs():
    return render_template('shift_logs.html')

@app.route('/api/shift-logs')
def get_shift_logs_data():
    return jsonify({
        "locations": {
            "mainland": {
                "kpis": get_today_kpis_shift_log(),
                "shifts": get_today_employee_shifts_mainland()
            },
            "floatingbar": {
                "kpis": get_today_kpis_shift_log_floatingbar(),
                "shifts": get_today_employee_shifts_floatingbar()
            }
        }
    })


# ---------------------------------------------------

#             4.) Food And Beverages

# ---------------------------------------------------
def get_monthly_food_beverages_kpis():
    try:
        #babalikan
        # response_menu = requests.get(FLOATING_API_URL_MENU)
        menu  = GLOBAL_DATA.get("menu", [])

        # response_transaction = requests.get(FLOATING_API_URL_TRANSACTION)
        transactions = GLOBAL_DATA.get("floating_transactions", [])

        current_month = datetime.now().month
        current_year = datetime.now().year

        total_items = len(menu)
        low_stock = 0

        for m in menu:
            availability = int(m.get("availability") or 0)
            if availability <= 10:
                low_stock += 1
        sales_map = {}
        fb_revenue = 0

        for t in transactions:
            if not t.get("created_at"):
                continue
            try:
                date_obj = datetime.strptime(t["created_at"],"%a, %d %b %Y %H:%M:%S %Z")
            except:
                continue

            if date_obj.month != current_month or date_obj.year != current_year:
                continue

            fb_revenue += float(t.get("total_net_billing") or 0)

            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                services = main_guest.get("services_availed", [])

                for item in services:
                    if item.get("is_void") is True:
                        continue
                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue
                    if name not in sales_map:
                        sales_map[name] = 0

                    sales_map[name] += qty 
                    
            add_on_guests = t.get("add_on_guest")
            if add_on_guests:
                if isinstance(add_on_guests, str):
                    add_on_guests = json.loads(add_on_guests)

                if isinstance(add_on_guests, list):
                    for guest in add_on_guests:
                        services = guest.get("services_availed", [])

                        for item in services:
                            if item.get("is_void") is True:
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            if name not in sales_map:
                                sales_map[name] = 0

                            sales_map[name] += qty                    
        top_seller = "N/A"
        if sales_map:
            top_seller = max(sales_map, key =sales_map.get)
        
        return {
            
                "total_items": f"{total_items}",
                "low_stock": f"{low_stock}",
                "top_seller": top_seller,
                "fb_revenue": f"₱{fb_revenue:,.2f}"
            
        }
    
            

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_weekly_food_beverages_kpis():
    try:
        #babalikan
        # response_menu = requests.get(FLOATING_API_URL_MENU)
        menu  = GLOBAL_DATA.get("menu", [])

        # response_transaction = requests.get(FLOATING_API_URL_TRANSACTION)
        transactions = GLOBAL_DATA.get("floating_transactions", [])

        current_week = datetime.now().isocalendar()[1]
        current_year = datetime.now().year

        total_items = len(menu)
        low_stock = 0

        for m in menu:
            availability = int(m.get("availability") or 0)
            if availability <= 10:
                low_stock += 1
        sales_map = {}
        fb_revenue = 0

        for t in transactions:
            if not t.get("created_at"):
                continue
            try:
                date_obj = datetime.strptime(t["created_at"],"%a, %d %b %Y %H:%M:%S %Z")
            except:
                continue
            txn_week = date_obj.isocalendar()[1]

            if txn_week != current_week or date_obj.year != current_year:
                continue

            fb_revenue += float(t.get("total_net_billing") or 0)

            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                services = main_guest.get("services_availed", [])

                for item in services:
                    if item.get("is_void") is True:
                        continue
                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue
                    if name not in sales_map:
                        sales_map[name] = 0

                    sales_map[name] += qty 
                    
            add_on_guests = t.get("add_on_guest")
            if add_on_guests:
                if isinstance(add_on_guests, str):
                    add_on_guests = json.loads(add_on_guests)

                if isinstance(add_on_guests, list):
                    for guest in add_on_guests:
                        services = guest.get("services_availed", [])

                        for item in services:
                            if item.get("is_void") is True:
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            if name not in sales_map:
                                sales_map[name] = 0

                            sales_map[name] += qty                    
        top_seller = "N/A"
        if sales_map:
            top_seller = max(sales_map, key =sales_map.get)
        
        return {
            
                "total_items": f"{total_items}",
                "low_stock": f"{low_stock}",
                "top_seller": top_seller,
                "fb_revenue": f"₱{fb_revenue:,.2f}"
            
        }
    
            

    except Exception as e:
            return {
        "total_items": 0,
        "low_stock": 0,
        "top_seller": "N/A",
        "fb_revenue": "₱0.00"
    }
    
def get_today_food_beverages_kpis():
    try:


        # Fetch data safely
        # menu_response = requests.get(FLOATING_API_URL_MENU)
        # transactions_response = requests.get(FLOATING_API_URL_TRANSACTION)

        menu = GLOBAL_DATA.get("menu", [])
        transactions = GLOBAL_DATA.get("floating_transactions", [])

        today = datetime.now().date()

        total_items = len(menu)
        low_stock = 0
        item_sales = {}
        total_revenue = 0

        # Optional: compute low stock (if needed)
        for m in menu:
            availability = int(m.get("availability") or 0)
            if availability <= 10:
                low_stock += 1

        # ---------------- DATE PARSER ----------------
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        return datetime.fromisoformat(date_str)
                    except:
                        return None

        # ---------------- PROCESS TRANSACTIONS ----------------
        for t in transactions:
            created_at = t.get("created_at")
            if not created_at:
                continue

            date_obj = parse_date(created_at)
            if not date_obj:
                continue

            # Filter TODAY
            if date_obj.date() != today:
                continue

            # Revenue
            total_revenue += float(t.get("total_net_billing") or 0)

            # ---------------- MAIN GUEST ----------------
            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                services = main_guest.get("services_availed", [])

                for item in services:
                    if item.get("is_void") is True:
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue

                    item_sales[name] = item_sales.get(name, 0) + qty

            # ---------------- ADD-ON GUESTS ----------------
            add_on_guests = t.get("add_on_guest")
            if add_on_guests:
                if isinstance(add_on_guests, str):
                    add_on_guests = json.loads(add_on_guests)

                if isinstance(add_on_guests, list):
                    for guest in add_on_guests:
                        services = guest.get("services_availed", [])

                        for item in services:
                            if item.get("is_void") is True:
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            item_sales[name] = item_sales.get(name, 0) + qty

        # ---------------- TOP SELLER ----------------
        top_seller = max(item_sales, key=item_sales.get) if item_sales else "N/A"

        return {
            "total_items": total_items,
            "low_stock": low_stock,
            "top_seller": top_seller,
            "fb_revenue": f"₱{total_revenue:,.2f}"
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "total_items": 0,
            "low_stock": 0,
            "top_seller": "N/A",
            "fb_revenue": "₱0.00"
        }


def get_monthly_food_beverages_charts():
    try:
        menu = GLOBAL_DATA.get("menu") or []
        transactions = GLOBAL_DATA.get("floating_transactions") or []

        current_month = datetime.now().month
        current_year = datetime.now().year

        # print(transactions)
        # ---------------------------
        # MENU MAP (for category)
        # ---------------------------
        menu_map = {}
        for m in menu:
            name = m.get("menu_name")
            category = m.get("category", "Unknown")

            if name:
                menu_map[name] = category

        # ---------------------------
        # WEEKLY REVENUE (Week 1–4)
        # ---------------------------
        weekly_totals = {
            "Week 1": 0,
            "Week 2": 0,
            "Week 3": 0,
            "Week 4": 0
        }

        category_count = {}

        for t in transactions:
            if not t.get("created_at"):
                continue

            try:
                date_obj = datetime.strptime(t["created_at"], "%a, %d %b %Y %H:%M:%S %Z")
            except:
                continue

            if date_obj.month != current_month or date_obj.year != current_year:
                continue


            day = date_obj.day
            if day <= 7:
                week = "Week 1"
            elif day <= 14:
                week = "Week 2"
            elif day <= 21:
                week = "Week 3"
            else:
                week = "Week 4"

            weekly_totals[week] += float(t.get("total_net_billing") or 0)

            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                for item in main_guest.get("services_availed", []):
                    if item.get("is_void"):
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue

                    category = menu_map.get(name, "Unknown")

                    if category not in category_count:
                        category_count[category] = 0

                    category_count[category] += qty

            add_on = t.get("add_on_guest")
            if add_on:
                if isinstance(add_on, str):
                    add_on = json.loads(add_on)

                if isinstance(add_on, list):
                    for guest in add_on:
                        for item in guest.get("services_availed", []):
                            if item.get("is_void"):
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            category = menu_map.get(name, "Unknown")

                            if category not in category_count:
                                category_count[category] = 0

                            category_count[category] += qty

        # ---------------------------
        # FORMAT OUTPUT
        # ---------------------------
        return {
            "revenue_trend": {
                "labels": list(weekly_totals.keys()),
                "data": list(weekly_totals.values())
            },
            "category_dist": {
                "labels": list(category_count.keys()),
                "data": list(category_count.values())
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def get_weekly_food_beverages_charts():
    try:
        menu = GLOBAL_DATA.get("menu") or []
        transactions = GLOBAL_DATA.get("floating_transactions") or []

        current_month = datetime.now().month
        current_year = datetime.now().year


        # ---------------------------
        # MENU MAP (for category)
        # ---------------------------
        menu_map = {}
        for m in menu:
            name = m.get("menu_name")
            category = m.get("category", "Unknown")

            if name:
                menu_map[name] = category

        # ---------------------------
        # WEEKLY REVENUE (Week 1–4)
        # ---------------------------
        weekly_totals = {
            "Week 1": 0,
            "Week 2": 0,
            "Week 3": 0,
            "Week 4": 0
        }

        category_count = {}

        for t in transactions:
            if not t.get("created_at"):
                continue

            try:
                date_obj = datetime.strptime(t["created_at"], "%a, %d %b %Y %H:%M:%S %Z")
            except:
                continue

            if date_obj.month != current_month or date_obj.year != current_year:
                continue


            day = date_obj.day
            if day <= 7:
                week = "Week 1"
            elif day <= 14:
                week = "Week 2"
            elif day <= 21:
                week = "Week 3"
            else:
                week = "Week 4"

            weekly_totals[week] += float(t.get("total_net_billing") or 0)

            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                for item in main_guest.get("services_availed", []):
                    if item.get("is_void"):
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue

                    category = menu_map.get(name, "Unknown")

                    if category not in category_count:
                        category_count[category] = 0

                    category_count[category] += qty

            add_on = t.get("add_on_guest")
            if add_on:
                if isinstance(add_on, str):
                    add_on = json.loads(add_on)

                if isinstance(add_on, list):
                    for guest in add_on:
                        for item in guest.get("services_availed", []):
                            if item.get("is_void"):
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            category = menu_map.get(name, "Unknown")

                            if category not in category_count:
                                category_count[category] = 0

                            category_count[category] += qty

        # ---------------------------
        # FORMAT OUTPUT
        # ---------------------------
        return {
            "revenue_trend": {
                "labels": list(weekly_totals.keys()),
                "data": list(weekly_totals.values())
            },
            "category_dist": {
                "labels": list(category_count.keys()),
                "data": list(category_count.values())
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_weekly_food_beverages_charts():
    try:
        menu = GLOBAL_DATA.get("menu") or []
        transactions = GLOBAL_DATA.get("floating_transactions") or []

        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # ---------------------------
        # MENU MAP
        # ---------------------------
        menu_map = {}
        for m in menu:
            name = m.get("menu_name")
            category = m.get("category", "Unknown")

            if name:
                menu_map[name] = category

        # ---------------------------
        # DAILY REVENUE (Sun–Sat)
        # ---------------------------
        days_order = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        daily_totals = {day: 0 for day in days_order}

        # ---------------------------
        # CATEGORY DISTRIBUTION
        # ---------------------------
        category_count = {}

        for t in transactions:
            if not t.get("created_at"):
                continue

            try:
                date_obj = datetime.strptime(t["created_at"], "%a, %d %b %Y %H:%M:%S %Z")
            except:
                continue

            if date_obj.date() < start_of_week.date() or date_obj.date() > end_of_week.date():
                continue

            # -------- DAY --------
            day_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_name = day_map[date_obj.weekday()]

            daily_totals[day_name] += float(t.get("total_net_billing") or 0)

            # -------- MAIN GUEST --------
            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                for item in main_guest.get("services_availed", []):
                    if item.get("is_void"):
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue

                    category = menu_map.get(name, "Unknown")

                    if category not in category_count:
                        category_count[category] = 0

                    category_count[category] += qty

            # -------- ADD-ON --------
            add_on = t.get("add_on_guest")
            if add_on:
                if isinstance(add_on, str):
                    add_on = json.loads(add_on)

                if isinstance(add_on, list):
                    for guest in add_on:
                        for item in guest.get("services_availed", []):
                            if item.get("is_void"):
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            category = menu_map.get(name, "Unknown")

                            if category not in category_count:
                                category_count[category] = 0

                            category_count[category] += qty

        return {
            "revenue_trend": {
                "labels": days_order,
                "data": [daily_totals[d] for d in days_order]
            },
            "category_dist": {
                "labels": list(category_count.keys()),
                "data": list(category_count.values())
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_daily_food_beverages_charts():
    try:
        menu = GLOBAL_DATA.get("menu") or []
        transactions = GLOBAL_DATA.get("floating_transactions") or []

        today = datetime.now().date()

        # ---------------------------
        # MENU MAP
        # ---------------------------
        menu_map = {}
        for m in menu:
            name = m.get("menu_name")
            category = m.get("category", "Unknown")

            if name:
                menu_map[name] = category

        # ---------------------------
        # HOURLY REVENUE (0–23)
        # ---------------------------
        hourly_totals = {f"{h:02}:00": 0 for h in range(24)}

        # ---------------------------
        # CATEGORY DISTRIBUTION
        # ---------------------------
        category_count = {}

        for t in transactions:
            if not t.get("created_at"):
                continue

            try:
                date_obj = datetime.strptime(t["created_at"], "%a, %d %b %Y %H:%M:%S %Z")
            except:
                continue

            if date_obj.date() != today:
                continue

            # -------- HOUR --------
            hour_label = f"{date_obj.hour:02}:00"
            hourly_totals[hour_label] += float(t.get("total_net_billing") or 0)

            # -------- MAIN GUEST --------
            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                for item in main_guest.get("services_availed", []):
                    if item.get("is_void"):
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue

                    category = menu_map.get(name, "Unknown")

                    if category not in category_count:
                        category_count[category] = 0

                    category_count[category] += qty

            # -------- ADD-ON --------
            add_on = t.get("add_on_guest")
            if add_on:
                if isinstance(add_on, str):
                    add_on = json.loads(add_on)

                if isinstance(add_on, list):
                    for guest in add_on:
                        for item in guest.get("services_availed", []):
                            if item.get("is_void"):
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            category = menu_map.get(name, "Unknown")

                            if category not in category_count:
                                category_count[category] = 0

                            category_count[category] += qty

        return {
            "revenue_trend": {
                "labels": list(hourly_totals.keys()),
                "data": list(hourly_totals.values())
            },
            "category_dist": {
                "labels": list(category_count.keys()),
                "data": list(category_count.values())
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def get_monthly_food_beverages_menu():
    try:
        menu = GLOBAL_DATA.get("menu") or []
        transactions = GLOBAL_DATA.get("floating_transactions") or []

        current_month = datetime.now().month
        current_year = datetime.now().year

        sales_map = {}

        for t in transactions:
            if not t.get("created_at"):
                continue

            try:
                date_obj = datetime.strptime(t["created_at"], "%a, %d %b %Y %H:%M:%S %Z")
            except:
                continue

            if date_obj.month != current_month or date_obj.year != current_year:
                continue

            # -------- MAIN GUEST --------
            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                for item in main_guest.get("services_availed", []):
                    if item.get("is_void") is True:
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue

                    if name not in sales_map:
                        sales_map[name] = 0

                    sales_map[name] += qty


            add_on = t.get("add_on_guest")
            if add_on:
                if isinstance(add_on, str):
                    add_on = json.loads(add_on)

                if isinstance(add_on, list):
                    for guest in add_on:
                        for item in guest.get("services_availed", []):
                            if item.get("is_void"):
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            if name not in sales_map:
                                sales_map[name] = 0

                            sales_map[name] += qty

        # ---------------------------
        # BUILD RESULT
        # ---------------------------
        result = []
        index = 1

        for m in menu:
            name = m.get("menu_name")
            category = m.get("category", "Unknown")
            item_type = m.get("type", "solid")
            price = float(m.get("unit_price") or 0)
            qty_available = int(m.get("availability") or 0)
            printer = m.get("kitchen_printer", "N/A")

            sold = sales_map.get(name, 0)

            # -------- TYPE --------
            if item_type == "drinkable":
                main_type = "Beverage"
            else:
                main_type = "Food"

            if qty_available == 0:
                status = "Sold Out"
                status_color = "text-red-700 bg-red-100"
            elif qty_available <= 10:
                status = "Low Stock"
                status_color = "text-orange-700 bg-orange-100"
            else:
                status = "Available"
                status_color = "text-green-700 bg-green-100"

            result.append({
                "id": f"ITM-{m.get('menu_id')}",
                "name": name,
                "category": category,
                "type": main_type,
                "price": f"{price:.2f}",
                "sold_month": sold,
                "qty": qty_available,
                "printer": printer,
                "status": status,
                "status_color": status_color
            })

            index += 1

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def get_weekly_food_beverages_menu():
    try:
        menu = GLOBAL_DATA.get("menu") or []
        transactions = GLOBAL_DATA.get("floating_transactions") or []

        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        sales_map = {}

        for t in transactions:
            if not t.get("created_at"):
                continue

            try:
                date_obj = datetime.strptime(
                    t["created_at"], "%a, %d %b %Y %H:%M:%S %Z"
                )
            except:
                continue

          
            if date_obj.date() < start_of_week.date() or date_obj.date() > end_of_week.date():
                continue

            # -------- MAIN GUEST --------
            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                for item in main_guest.get("services_availed", []):
                    if item.get("is_void") is True:
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue

                    if name not in sales_map:
                        sales_map[name] = 0

                    sales_map[name] += qty

            # -------- ADD-ON GUEST --------
            add_on = t.get("add_on_guest")
            if add_on:
                if isinstance(add_on, str):
                    add_on = json.loads(add_on)

                if isinstance(add_on, list):
                    for guest in add_on:
                        for item in guest.get("services_availed", []):
                            if item.get("is_void"):
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            if name not in sales_map:
                                sales_map[name] = 0

                            sales_map[name] += qty

        # ---------------------------
        # BUILD RESULT (SAME AS MONTHLY)
        # ---------------------------
        result = []
        index = 1

        for m in menu:
            name = m.get("menu_name")
            category = m.get("category", "Unknown")
            item_type = m.get("type", "solid")
            price = float(m.get("unit_price") or 0)
            qty_available = int(m.get("availability") or 0)
            printer = m.get("kitchen_printer", "N/A")

            sold = sales_map.get(name) or 0

            # -------- TYPE --------
            if item_type == "drinkable":
                main_type = "Beverage"
            else:
                main_type = "Food"

            # -------- STATUS --------
            if qty_available == 0:
                status = "Sold Out"
                status_color = "text-red-700 bg-red-100"
            elif qty_available <= 10:
                status = "Low Stock"
                status_color = "text-orange-700 bg-orange-100"
            else:
                status = "Available"
                status_color = "text-green-700 bg-green-100"

            result.append({
                "id": f"ITM-{m.get('menu_id')}",
                "name": name,
                "category": category,
                "type": main_type,
                "price": f"{price:.2f}",
                "sold_month": sold,   #sold week to ginanyan ko lang para di na babaguhin front ni arjun HAHAHA
                "qty": qty_available,
                "printer": printer,
                "status": status,
                "status_color": status_color
            })

            index += 1

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def get_today_food_beverages_menu():
    try:
        menu = GLOBAL_DATA.get("menu") or []
        transactions = GLOBAL_DATA.get("floating_transactions") or []

        today = datetime.now().date()

        sales_map = {}

        for t in transactions:
            if not t.get("created_at"):
                continue

            try:
                date_obj = datetime.strptime(
                    t["created_at"],
                    "%a, %d %b %Y %H:%M:%S %Z"
                )
            except:
                continue

            
            if date_obj.date() != today:
                continue

            # -------- MAIN GUEST --------
            main_guest = t.get("main_guest_information")
            if main_guest:
                if isinstance(main_guest, str):
                    main_guest = json.loads(main_guest)

                for item in main_guest.get("services_availed", []):
                    if item.get("is_void") is True:
                        continue

                    name = item.get("item")
                    qty = int(item.get("qty") or 0)

                    if not name:
                        continue

                    if name not in sales_map:
                        sales_map[name] = 0

                    sales_map[name] += qty

            # -------- ADD-ON GUEST --------
            add_on = t.get("add_on_guest")
            if add_on:
                if isinstance(add_on, str):
                    add_on = json.loads(add_on)

                if isinstance(add_on, list):
                    for guest in add_on:
                        for item in guest.get("services_availed", []):
                            if item.get("is_void"):
                                continue

                            name = item.get("item")
                            qty = int(item.get("qty") or 0)

                            if not name:
                                continue

                            if name not in sales_map:
                                sales_map[name] = 0

                            sales_map[name] += qty

        # ---------------------------
        # BUILD RESULT
        # ---------------------------
        result = []
        index = 1

        for m in menu:
            name = m.get("menu_name")
            category = m.get("category", "Unknown")
            item_type = m.get("type", "solid")
            price = float(m.get("unit_price") or 0)
            qty_available = int(m.get("availability") or 0)
            printer = m.get("kitchen_printer", "N/A")

            sold = sales_map.get(name, 0)

            # TYPE
            if item_type == "drinkable":
                main_type = "Beverage"
            else:
                main_type = "Food"

            # STATUS
            if qty_available == 0:
                status = "Sold Out"
                status_color = "text-red-700 bg-red-100"
            elif qty_available <= 10:
                status = "Low Stock"
                status_color = "text-orange-700 bg-orange-100"
            else:
                status = "Available"
                status_color = "text-green-700 bg-green-100"

            result.append({
                "id": f"ITM-{m.get('menu_id')}",
                "name": name,
                "category": category,
                "type": main_type,
                "price": f"{price:.2f}",
                "sold_month": sold, 
                "qty": qty_available,
                "printer": printer,
                "status": status,
                "status_color": status_color
            })

            index += 1

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

FB_DATA = {
    "month": {
        # "kpis": {
        #     "total_items": "124", "low_stock": "8", "top_seller": "Grilled Salmon", "fb_revenue": "₱142,500.00"
        # },
        "kpis": get_monthly_food_beverages_kpis(),

        # "charts": {
        #     "revenue_trend": {"labels": ["Week 1", "Week 2", "Week 3", "Week 4"], "data": [28000, 35000, 32000, 47500]},
        #     "category_dist": {"labels": ["Mains", "Cocktails", "Appetizers", "Drinks"], "data": [45, 25, 15, 15]}
        # },
        "charts" : get_monthly_food_beverages_charts(),
        # "menu": [
        #     {"id": "ITM-001", "name": "Grilled Salmon", "category": "Mains", "type": "Food", "price": "450.00", "sold_month": 342, "qty": 15, "printer": "MAINS", "status": "Available", "status_color": "text-green-700 bg-green-100"},
        #     {"id": "ITM-002", "name": "Ocean Blue Margarita", "category": "Signature Cocktails", "type": "Beverage", "price": "280.00", "sold_month": 215, "qty": 4, "printer": "BAR", "status": "Low Stock", "status_color": "text-orange-700 bg-orange-100"},
        #     {"id": "ITM-003", "name": "Truffle Fries", "category": "Appetizers", "type": "Food", "price": "180.00", "sold_month": 450, "qty": 0, "printer": "MAINS", "status": "Sold Out", "status_color": "text-red-700 bg-red-100"},
        #     {"id": "ITM-004", "name": "Wagyu Burger", "category": "Mains", "type": "Food", "price": "380.00", "sold_month": 189, "qty": 20, "printer": "MAINS", "status": "Available", "status_color": "text-green-700 bg-green-100"},
        #     {"id": "ITM-005", "name": "Mango Graham Shake", "category": "Drinks", "type": "Beverage", "price": "150.00", "sold_month": 310, "qty": 12, "printer": "BAR", "status": "Available", "status_color": "text-green-700 bg-green-100"}
        # ]
        "menu" : get_monthly_food_beverages_menu()
    },
    "week": {
        # "kpis": {
        #     "total_items": "124", "low_stock": "5", "top_seller": "Truffle Fries", "fb_revenue": "₱34,200.00"
        # },
        "kpis": get_weekly_food_beverages_kpis(),
        # "charts": {
        #     "revenue_trend": {"labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "data": [4200, 3800, 4100, 5000, 6800, 7500, 2800]},
        #     "category_dist": {"labels": ["Mains", "Cocktails", "Appetizers", "Drinks"], "data": [35, 30, 25, 10]}
        # },
        "charts": get_weekly_food_beverages_charts(),
        # "menu": [
        #     {"id": "ITM-001", "name": "Grilled Salmon", "category": "Mains", "type": "Food", "price": "450.00", "sold_month": 84, "qty": 15, "printer": "MAINS", "status": "Available", "status_color": "text-green-700 bg-green-100"},
        #     {"id": "ITM-002", "name": "Ocean Blue Margarita", "category": "Signature Cocktails", "type": "Beverage", "price": "280.00", "sold_month": 62, "qty": 4, "printer": "BAR", "status": "Low Stock", "status_color": "text-orange-700 bg-orange-100"},
        #     {"id": "ITM-003", "name": "Truffle Fries", "category": "Appetizers", "type": "Food", "price": "180.00", "sold_month": 110, "qty": 0, "printer": "MAINS", "status": "Sold Out", "status_color": "text-red-700 bg-red-100"},
        #     {"id": "ITM-004", "name": "Wagyu Burger", "category": "Mains", "type": "Food", "price": "380.00", "sold_month": 45, "qty": 20, "printer": "MAINS", "status": "Available", "status_color": "text-green-700 bg-green-100"},
        #     {"id": "ITM-005", "name": "Mango Graham Shake", "category": "Drinks", "type": "Beverage", "price": "150.00", "sold_month": 76, "qty": 12, "printer": "BAR", "status": "Available", "status_color": "text-green-700 bg-green-100"}
        # ]
        "menu" : get_weekly_food_beverages_menu()
    },
    "day": {
        # "kpis": {
        #     "total_items": "124", "low_stock": "2", "top_seller": "Mango Graham Shake", "fb_revenue": "₱6,400.00"
        # },
        "kpis": get_today_food_beverages_kpis(),
        # "charts": {
        #     "revenue_trend": {"labels": ["10AM", "12PM", "2PM", "4PM", "6PM", "8PM", "10PM"], "data": [500, 1200, 800, 600, 1500, 2000, 800]},
        #     "category_dist": {"labels": ["Mains", "Cocktails", "Appetizers", "Drinks"], "data": [20, 15, 25, 40]}
        # },
        "charts": get_daily_food_beverages_charts(),
        # "menu": [
        #     {"id": "ITM-001", "name": "Grilled Salmon", "category": "Mains", "type": "Food", "price": "450.00", "sold_month": 12, "qty": 15, "printer": "MAINS", "status": "Available", "status_color": "text-green-700 bg-green-100"},
        #     {"id": "ITM-002", "name": "Ocean Blue Margarita", "category": "Signature Cocktails", "type": "Beverage", "price": "280.00", "sold_month": 8, "qty": 4, "printer": "BAR", "status": "Low Stock", "status_color": "text-orange-700 bg-orange-100"},
        #     {"id": "ITM-003", "name": "Truffle Fries", "category": "Appetizers", "type": "Food", "price": "180.00", "sold_month": 15, "qty": 0, "printer": "MAINS", "status": "Sold Out", "status_color": "text-red-700 bg-red-100"},
        #     {"id": "ITM-004", "name": "Wagyu Burger", "category": "Mains", "type": "Food", "price": "380.00", "sold_month": 5, "qty": 20, "printer": "MAINS", "status": "Available", "status_color": "text-green-700 bg-green-100"},
        #     {"id": "ITM-005", "name": "Mango Graham Shake", "category": "Drinks", "type": "Beverage", "price": "150.00", "sold_month": 22, "qty": 12, "printer": "BAR", "status": "Available", "status_color": "text-green-700 bg-green-100"}
        # ]
        "menu": get_today_food_beverages_menu()
    }
}

@app.route("/food-beverage", methods=["POST"])
def post_food_beverage():
    try:
        data = request.get_json()

        response = requests.post(
            FLOATING_API_URL_MENU,  
            json = {
                "menu_name": data.get("name"),
                "category": data.get("category"),
                "kitchen_printer": data.get("printer"),
                "unit_price": float(data.get("price") or 0),
                "recipe": None,
                "availability": int(data.get("qty") or 0),
                "type": "solid" if data.get("type") == "Food" else "drinkable",
                "picture_url": None
            }
        )
        

        return response.json(), response.status_code

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.route("/floatingbar/menu/<int:menu_id>", methods=["PUT"])
def update_menu(menu_id):
    try:
        data = request.get_json()

        payload = {
            "menu_name": data.get("name"),
            "category": data.get("category"),
            "kitchen_printer": data.get("printer"),
            "unit_price": float(data.get("price") or 0),
            "recipe": None,
            "availability": int(data.get("qty") or 0),
            "type": "solid" if data.get("type") == "Food" else "drinkable",
            "picture_url": None
        }

       
        response = requests.put(
            f"{FLOATING_API_URL_MENU}/{menu_id}",
            json=payload
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route("/floatingbar/menu/<int:menu_id>", methods=["DELETE"])
def delete_menu(menu_id):
    try:
        if not menu_id:
            return jsonify({"status": "error", "message" : "walang id tanga pano mo madedelete"})
        response = requests.delete(f"{FLOATING_API_URL_MENU}/{menu_id}")
       
        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/food-beverage')
def food_beverage():
    return render_template('food_beverage.html')

# @app.route('/api/food-beverage')
# def get_fb_data():
#     # load_all_data()
#     # Grab the 'time' query parameter (defaults to 'month' if not provided)
#     timeframe = request.args.get('time', 'month')
    
#     # Return the data for the specific timeframe. 
#     # If a weird timeframe is requested, fallback to 'month'
#     data = FB_DATA.get(timeframe, FB_DATA['month'])
    
#     return jsonify(data)

@app.route('/api/food-beverage')
def get_fb_data():
    timeframe = request.args.get('time', 'month')

    if timeframe == "day":
        return jsonify({
            "kpis": get_today_food_beverages_kpis(),
            "charts": get_daily_food_beverages_charts(),
            "menu": get_today_food_beverages_menu()
        })

    elif timeframe == "week":
        return jsonify({
            "kpis": get_weekly_food_beverages_kpis(),
            "charts": get_weekly_food_beverages_charts(),
            "menu": get_weekly_food_beverages_menu()
        })

    else:  # default = month
        return jsonify({
            "kpis": get_monthly_food_beverages_kpis(),
            "charts": get_monthly_food_beverages_charts(),
            "menu": get_monthly_food_beverages_menu()
        })

# ------------------------------------------------


#                7.) USER MANAGEMENT


# ------------------------------------------------
def get_employees_data_users():
    try:
        mainland_employees = GLOBAL_DATA.get("mainland_employees", [])

        # floatingbar_employees_response  = requests.get(FLOATING_API_URL_EMPLOYEES)
        floatingbar_employees = GLOBAL_DATA.get("floating_employees", [])

        employees = mainland_employees + floatingbar_employees
        
        users = []

        for emp in employees:
            users.append({
                "id": emp.get("employee_id"),
                "firstName": emp.get("firstName"),
                "lastName" : emp.get("lastName"),
                "name": emp.get("firstName") + " " + emp.get("lastName"),
                "role" : emp.get("position"),
                "department": emp.get("department"),
                "status": emp.get("status"),
                "status_color" : "text-green-700 bg-green-100" if emp.get("status") == "Active" else "text-gray-700 bg-gray-100",
                "last_login" : emp.get("last_login") or "N/A",
                "email" : emp.get("email"),
                "password": emp.get("password"),
                "contact_number": emp.get("contact_number")
             })
        return users

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_employees_data_kpis():
    try:
        mainland_employees = get_mainland_employee()

        floatingbar_employees_response  = requests.get(FLOATING_API_URL_EMPLOYEES)
        data = floatingbar_employees_response.json()

        

        employees = mainland_employees + data
        active = 0
        Managers = 0
        Cashiers = 0 

        for m in employees:
            if m.get("position").lower() == "manager":
                Managers += 1
            if m.get("position").lower() == "cashier":
                Cashiers += 1
            if m.get("status").lower() == "active":
                active += 1
        return {
            "total_users": len(employees),
            "active_now": active,
            "managers": Managers,
            "cashiers": Cashiers
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

USER_DATA = {
    # "kpis": {
    #     "total_users": "14",
    #     "active_now": "6",
    #     "managers": "2",
    #     "cashiers": "5"
    # },
    "kpis": get_employees_data_kpis(),
    # "users": [
    #     {"id": "EMP-001", "name": "Juan Dela Cruz", "role": "Manager", "department": "Admin", "status": "Active", "status_color": "text-green-700 bg-green-100", "last_login": "Today, 08:00 AM"},
    #     {"id": "EMP-002", "name": "Lucille Marfa", "role": "Cashier", "department": "Mainland", "status": "Active", "status_color": "text-green-700 bg-green-100", "last_login": "Today, 07:45 AM"},
    #     {"id": "EMP-003", "name": "Jarek Melgar", "role": "Cashier", "department": "Skydeck", "status": "Offline", "status_color": "text-gray-700 bg-gray-100", "last_login": "Yesterday, 05:00 PM"},
    #     {"id": "EMP-004", "name": "Vlad Navarro", "role": "Waiter", "department": "Skydeck", "status": "Active", "status_color": "text-green-700 bg-green-100", "last_login": "Today, 10:00 AM"}
    # ]
    "users": get_employees_data_users()
}

@app.route("/employee", methods=["POST"])
def post_employee():
    try:
        employee_data = request.get_json()

        if not employee_data:
            return jsonify({
                "status": "error",
                "message": "No input data provided"
            }), 400

        department = (employee_data.get("department") or "").lower()

        if department == "floating bar":
            response = requests.post(FLOATING_API_URL_EMPLOYEES, json=employee_data)

            if response.status_code in [200, 201]:
                return jsonify({
                    "status": "success",
                    "message": "Employee sent to Floating Bar"
                }), 201
            else:
                return jsonify({
                    "status": "error",
                    "message": "Failed to send to Floating Bar",
                    "details": response.text
                }), 500

    
        elif department == "mainland":
            result = post_mainland_employee(employee_data)

            if result["status"] == "success":
                return jsonify(result), 201
            else:
                return jsonify(result), 500

    
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid department"
            }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@app.route("/employee/<string:employee_id>", methods=["PUT"])
def update_employee(employee_id):
    try:
        employee_data = request.get_json()

        if not employee_data:
            return jsonify({
                "status": "error",
                "message": "No input data provided"
            }), 400

        department = (employee_data.get("department") or "").lower()
        if "floating" in department:
            response = requests.put(
                f"{FLOATING_API_URL_EMPLOYEES}/{employee_id}",
                json=employee_data
            )

            if response.status_code in [200, 201]:
                return jsonify({
                    "status": "success",
                    "message": "Floating Bar employee updated"
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Failed to update Floating Bar employee",
                    "details": response.text
                }), 500

        elif "mainland" in department:
            result = put_mainland_employee_by_id(employee_id, employee_data)

            if result["status"] == "success":
                return jsonify(result)
            else:
                return jsonify(result), 500
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid department"
            }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@app.route("/employee/<string:employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
    try:
        if not employee_id:
            return jsonify({
                "status": "error",
                "message": "Employee ID is required"
            }), 400


        mainland_employee = get_mainland_employee_by_emp_id(employee_id)

        if mainland_employee:
            result = delete_mainland_employee(employee_id)

            if result.get("status") == "success":
                return jsonify({
                    "status": "success",
                    "message": "Employee deleted from Mainland"
                })

            return jsonify(result), 500


        response = requests.delete(
            f"{FLOATING_API_URL_EMPLOYEES}/{employee_id}"
        )

        if response.status_code in [200, 204]:
            return jsonify({
                "status": "success",
                "message": "Employee deleted from Floating Bar"
            })

        return jsonify({
            "status": "error",
            "message": "Employee not found in either Mainland or FloatingBar"
        }), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500   

@app.route('/user-management')
def user_management():
    return render_template('user_management.html')

@app.route('/api/users')
def get_user_data():
    return jsonify({
        "kpis": get_employees_data_kpis(),
        "users": get_employees_data_users()
    })
if __name__ == '__main__':
    app.run(debug=True, port=8002)