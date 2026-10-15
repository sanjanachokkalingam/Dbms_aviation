
from db import get_connection

connection = None
cursor = None

try:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            c.TABLE_NAME,
            c.CONSTRAINT_NAME,
            c.CONSTRAINT_TYPE,
            cc.COLUMN_NAME,
            r.TABLE_NAME AS REFERENCED_TABLE
        FROM USER_CONSTRAINTS c
        JOIN USER_CONS_COLUMNS cc
          ON c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
         AND c.TABLE_NAME = cc.TABLE_NAME
        LEFT JOIN USER_CONSTRAINTS r
          ON c.R_CONSTRAINT_NAME = r.CONSTRAINT_NAME
        WHERE c.TABLE_NAME IN (
            'MAINTENANCE_RECORD',
            'INSPECTION_CHECKLIST',
            'MAINTENANCE_SCHEDULE'
        )
        AND c.CONSTRAINT_TYPE IN ('P', 'R', 'U')
        ORDER BY c.TABLE_NAME, c.CONSTRAINT_TYPE, cc.POSITION
    """)

    print("TABLE | CONSTRAINT | TYPE | COLUMN | REFERENCES")

    for row in cursor.fetchall():
        print(row)

except Exception as error:
    print("Error:", error)

finally:
    if cursor is not None:
        cursor.close()

    if connection is not None:
        connection.close()
