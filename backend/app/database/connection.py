from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.models.database import Base
from app.config import settings
import os
from pathlib import Path

# Create data directory in your project root
project_root = Path(__file__).parent.parent.parent  # Go up to project root
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)

# Database path
db_path = data_dir / "pulse.db"

# Database URLs
DATABASE_URL = f"sqlite:///{db_path}"
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

print(f"Database path: {db_path}")

# Create engines
sync_engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=sync_engine)
        print(f"Database tables created successfully at {db_path}")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Database directory: {data_dir}")
        print(f"Directory exists: {data_dir.exists()}")
        print(f"Directory permissions: {oct(os.stat(data_dir).st_mode)}")
        raise

async def get_async_session():
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_session():
    """Get sync database session for background tasks"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()