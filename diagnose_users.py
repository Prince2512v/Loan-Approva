
import os
import sqlite3

BASE_DIR = r"c:\Users\ASUS\Downloads\Loan-Approval-Prediction-main1.0\Loan-Approval-Prediction-main"
DB_PATH = os.path.join(BASE_DIR, 'database', 'loans.db')

def diagnose():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- User Records ---")
    cursor.execute("SELECT id, username, email, length(password_hash) FROM user")
    users = cursor.fetchall()
    for user in users:
        print(f"ID: {user[0]} | Username: {user[1]} | Email: {user[2]} | Pass Hash Len: {user[3]}")

    conn.close()

if __name__ == "__main__":
    diagnose()
