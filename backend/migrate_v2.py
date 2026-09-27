from sqlalchemy import text
from backend.database import SessionLocal

db = SessionLocal()
sqls = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100) DEFAULT 'Engineering';",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS organization VARCHAR(100) DEFAULT 'ProCom';",
    "ALTER TABLE messages ADD COLUMN IF NOT EXISTS file_url VARCHAR(500) DEFAULT '';",
    "ALTER TABLE messages ADD COLUMN IF NOT EXISTS file_name VARCHAR(255) DEFAULT '';",
    "ALTER TABLE messages ADD COLUMN IF NOT EXISTS file_type VARCHAR(50) DEFAULT '';",
    "ALTER TABLE messages ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0;",
    "ALTER TABLE messages ADD COLUMN IF NOT EXISTS reactions_json TEXT DEFAULT '{}';"
]

for s in sqls:
    try:
        db.execute(text(s))
        db.commit()
        print("Executed:", s)
    except Exception as e:
        print("Error:", e)
        db.rollback()

db.close()
print("Migration completed!")
