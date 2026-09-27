import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current working dir and backend directory
load_dotenv()
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

# Default Neon PostgreSQL connection string:
DEFAULT_NEON_URL = "postgresql://neondb_owner:npg_5XeHTZLVw1Oo@ep-delicate-fire-b4s8apcf-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
NEON_DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_NEON_URL).strip()

# Resilient Engine Setup:
# If DATABASE_URL is provided, test and use PostgreSQL (Neon).
# Otherwise or if PostgreSQL connection fails, fallback seamlessly to local SQLite.
db_type = "sqlite"
engine = None

# SQLite path - use /tmp on Vercel serverless environment
sqlite_path = "/tmp/chatspace.db" if os.environ.get("VERCEL") else "./chatspace.db"

if NEON_DATABASE_URL and ("postgres" in NEON_DATABASE_URL or "neon.tech" in NEON_DATABASE_URL):
    try:
        # Check if URL starts with postgres:// and convert to postgresql:// for SQLAlchemy
        clean_url = NEON_DATABASE_URL
        if clean_url.startswith("postgres://"):
            clean_url = clean_url.replace("postgres://", "postgresql://", 1)
        
        # Ensure sslmode for Neon if not present
        if "neon.tech" in clean_url and "sslmode" not in clean_url:
            separator = "&" if "?" in clean_url else "?"
            clean_url = f"{clean_url}{separator}sslmode=require"
            
        test_engine = create_engine(
            clean_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"connect_timeout": 5}
        )
        # Test connection
        with test_engine.connect() as conn:
            pass
        engine = test_engine
        db_type = "neon_postgresql"
        print("[DATABASE] Successfully connected to Neon PostgreSQL!")
    except Exception as e:
        print(f"[DATABASE WARNING] Could not connect to provided Neon PostgreSQL URL: {e}")
        print(f"[DATABASE] Gracefully falling back to SQLite database ({sqlite_path})...")
        engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
        db_type = "sqlite_fallback"
else:
    print(f"[DATABASE] Initializing SQLite database ({sqlite_path})...")
    engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
    db_type = "sqlite"


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_status():
    is_neon = "neon" in db_type
    masked_url = ""
    if NEON_DATABASE_URL:
        # Mask credentials for privacy
        parts = NEON_DATABASE_URL.split("@")
        if len(parts) > 1:
            masked_url = f"postgresql://****@{parts[1]}"
        else:
            masked_url = "postgresql://****"
            
    return {
        "engine_type": db_type,
        "is_neon": is_neon,
        "connected": True,
        "database_url_configured": bool(NEON_DATABASE_URL),
        "masked_url": masked_url,
        "guide": "To connect your Neon PostgreSQL database, add DATABASE_URL=postgresql://... in backend/.env"
    }
