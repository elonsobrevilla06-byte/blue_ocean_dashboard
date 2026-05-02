from db_connector import get_connection_mainland

def get_access_price(access_type, deck):
    conn = get_connection_mainland()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM access_pricing WHERE access_type = %s AND deck = %s",
        (access_type, deck)
    )
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result