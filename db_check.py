import sqlite3
import os

db_path = 'users.db'
print(f"Checking {db_path}...")
if not os.path.exists(db_path):
    print(f"Database {db_path} does not exist at this path.")
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coupons'")
    if c.fetchone():
        print("Coupons table exists.")
        c.execute("SELECT * FROM coupons")
        rows = c.fetchall()
        print(f"Rows ({len(rows)}):")
        for row in rows:
            print(row)
    else:
        print("Coupons table does not exist.")
    conn.close()
