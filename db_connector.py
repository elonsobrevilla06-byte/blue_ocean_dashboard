import mysql.connector

def get_connection_mainland():
    return mysql.connector.connect(
        host = "10.104.120.251",
        user = "root",
        password = "mainland@bob2026!",
        database = "blue_ocean_mainland_db"

    )

def get_connection_floatingbar():
    return mysql.connector.connect(
        host = "10.104.120.251",
        user = "root",
        password = "mainland@bob2026!",
        database = "blue_ocean_floatingbar_db"
    )

def test_mainland_connection():
    conn = get_connection_mainland()
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE();")
    db_name = cursor.fetchone()
    print(f"Mainland DB Connected: {db_name}")

    cursor.close()
    conn.close()


def test_floatingbar_connection():
    conn = get_connection_floatingbar()
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE();")
    db_name = cursor.fetchone()
    print(f"Floatingbar DB Connected: {db_name}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_mainland_connection()
    test_floatingbar_connection()
