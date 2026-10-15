
from db import get_connection

connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT
        SYS_CONTEXT('USERENV', 'SERVICE_NAME'),
        SYS_CONTEXT('USERENV', 'INSTANCE_NAME'),
        SYS_CONTEXT('USERENV', 'CON_NAME')
    FROM DUAL
""")

result = cursor.fetchone()

print("Service name:", result[0])
print("Instance name:", result[1])
print("Container name:", result[2])

cursor.close()
connection.close()

