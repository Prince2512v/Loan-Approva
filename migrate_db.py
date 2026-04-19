import sqlite3
import os

# Path to the database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'loans.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'otp' not in columns:
            print("Adding 'otp' column to 'user' table...")
            cursor.execute("ALTER TABLE user ADD COLUMN otp VARCHAR(6)")
        
        if 'otp_expiry' not in columns:
            print("Adding 'otp_expiry' column to 'user' table...")
            cursor.execute("ALTER TABLE user ADD COLUMN otp_expiry DATETIME")

        conn.commit()
        print("Migration successful!")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
