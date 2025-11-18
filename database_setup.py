import sqlite3

# Create SQLite database
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Create table (username, email, password)
c.execute('''CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    email TEXT,
    password TEXT
)''')

conn.commit()
conn.close()

print("✅ Database (with email) created successfully!")
