import sqlite3

conn = sqlite3.connect('C:/Users/Administrator/ai-digital-human/backend/database.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print("Tables:", tables)

for table in tables:
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cur.fetchall()]
    print(f"{table}: {columns}")

conn.close()