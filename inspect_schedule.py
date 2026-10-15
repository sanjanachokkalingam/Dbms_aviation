
from db import get_connection

connection = get_connection()
cursor = connection.cursor()

try:
    cursor.execute("""
        SELECT column_name, data_type, nullable
        FROM user_tab_columns
        WHERE table_name = 'SPARE_PART'
        ORDER BY column_id
    """)

    print("\n--- SPARE_PART TABLE COLUMNS ---")

    for column in cursor.fetchall():
        print(column)

    cursor.execute("SELECT * FROM SPARE_PART")

    print("\n--- EXISTING SPARE PARTS ---")
    print("Column names:", [col[0] for col in cursor.description])

    rows = cursor.fetchall()

    if rows:
        for row in rows:
            print(row)
    else:
        print("No spare parts found.")

finally:
    cursor.close()
    connection.close()

