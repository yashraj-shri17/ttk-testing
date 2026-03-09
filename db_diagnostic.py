import sqlite3
import os
import sys
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
try:
    import psycopg2
except ImportError:
    psycopg2 = None
USE_POSTGRES = bool(DATABASE_URL and psycopg2)

def check_coupons():
    print(f"--- DB STATUS ---")
    print(f"Mode: {'POSTGRES' if USE_POSTGRES else 'SQLITE'}")
    print(f"URL: {DATABASE_URL[:20]}..." if DATABASE_URL else "No URL")
    
    conn = None
    try:
        if USE_POSTGRES:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect("users.db")
        
        c = conn.cursor()
        
        print("\n--- TABLES ---")
        if USE_POSTGRES:
            c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        else:
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        for t in tables:
            print(f"- {t[0]}")
            
        print("\n--- COUPONS DATA ---")
        try:
            c.execute("SELECT * FROM coupons")
            columns = [desc[0] for desc in c.description]
            print(f"Columns: {columns}")
            rows = c.fetchall()
            print(f"Total Rows: {len(rows)}")
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error reading coupons: {e}")
            
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_coupons()
