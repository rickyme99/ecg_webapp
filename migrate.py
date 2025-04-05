import sqlite3

# Connect to your database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create the uploads table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    filename TEXT,
    upload_date TEXT,
    result_path TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
''')

conn.commit()
conn.close()

print("✅ uploads table added (if not already there).")
