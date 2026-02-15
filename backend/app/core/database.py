import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger("hr-api")

MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds


def create_engine_with_retry():
    """Create SQLAlchemy engine and verify DB connection with retries."""
    eng = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,          # Auto-reconnect stale connections
        pool_recycle=300,             # Recycle connections every 5 min
        pool_size=5,
        max_overflow=10,
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"✅ Database connected (attempt {attempt})")
            return eng
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"⏳ DB not ready (attempt {attempt}/{MAX_RETRIES}): {e}")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"❌ Could not connect to DB after {MAX_RETRIES} attempts")
                raise
    return eng


engine = create_engine_with_retry()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
