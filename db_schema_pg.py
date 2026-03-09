import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(os.environ['DATABASE_URL'])
c = conn.cursor()
c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'coupons';")
cols = c.fetchall()
print("Postgres coupons columns:")
for col in cols:
    print(col)
conn.close()
