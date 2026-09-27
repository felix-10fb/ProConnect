from sqlalchemy import text
from backend.database import SessionLocal

db = SessionLocal()
tables = ['users', 'conversations', 'conversation_members', 'community_channels', 'messages', 'reminders', 'meetings', 'call_logs']
for tbl in tables:
    try:
        db.execute(text(f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), COALESCE((SELECT MAX(id) FROM {tbl}), 1));"))
        print(f"Synced sequence for {tbl}")
    except Exception as e:
        print(f"Error for {tbl}: {e}")
db.commit()
db.close()
print("All sequences synchronized!")
