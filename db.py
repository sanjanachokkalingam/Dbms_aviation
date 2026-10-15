
import os
import oracledb
from dotenv import load_dotenv

# Load settings from the .env file in this project's folder
load_dotenv(override=True)

def get_connection():
    connection = oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn=os.getenv("DB_DSN")
    )
    return connection
