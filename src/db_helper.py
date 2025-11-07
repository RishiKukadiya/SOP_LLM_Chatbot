import pyodbc
import os
from dotenv import load_dotenv

# ---------------- LOAD ENVIRONMENT ----------------
load_dotenv()

def get_connection():
    """Connects to SQL Server using environment variables."""
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')}"
        )
        print("✅ Database connected successfully.")
        return conn
    except Exception as e:
        print("❌ Database connection error:", e)
        return None


def validate_user(email, password):
    """
    Validates user login from SQL Server employee table.
    Adjust table/column names as per your actual database schema.
    """
    conn = get_connection()
    if conn is None:
        print("❌ Could not connect to database.")
        return False

    try:
        cursor = conn.cursor()

        # 🔹 Verify available columns
        cursor.execute("SELECT TOP 5 * FROM Employee_data")
        rows = cursor.fetchall()
        print("🧩 DEBUG — First 5 rows from Employee_data:")
        for r in rows:
            print(r)

        # 🔹 Use correct table and column names
        query = """
        SELECT COUNT(*) 
        FROM Employee_data
        WHERE RTRIM(LTRIM(email)) = ? AND RTRIM(LTRIM(password)) = ?
        """
        cursor.execute(query, (email.strip(), password.strip()))
        result = cursor.fetchone()[0]

        print(f"DEBUG: email={email}, password={password}, result={result}")

        cursor.close()
        conn.close()
        return result > 0

    except Exception as e:
        print("❌ SQL Error:", e)
        return False
