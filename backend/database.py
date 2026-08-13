"""
Sawa Digital Tech Solutions Database Configuration
SQLAlchemy setup with SQLite database
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Database URL - SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./sawadigitaltech.db"
)

# Create SQLAlchemy engine
# connect_args is needed for SQLite to handle foreign keys
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"  # Log SQL queries in development
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    Used with FastAPI's dependency injection system
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables
    Creates all tables defined in models
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """
    Drop all database tables
    WARNING: This will delete all data!
    Use only for testing or development reset
    """
    Base.metadata.drop_all(bind=engine)


def reset_db() -> None:
    """
    Reset database - drop and recreate all tables
    WARNING: This will delete all data!
    """
    drop_all_tables()
    init_db()


# Database connection utilities
def check_db_connection() -> bool:
    """
    Check if database connection is working
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False


def get_db_info() -> dict:
    """
    Get database connection information
    
    Returns:
        dict: Database connection details
    """
    return {
        "database_url": DATABASE_URL,
        "engine": str(engine.url),
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else "N/A",
        "connected": check_db_connection()
    }