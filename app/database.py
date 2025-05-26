from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import contextmanager
from .config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        
@contextmanager
def get_db_context():
    """Context manager to handle database sessions."""
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        
def get_locked_wallet(db: Session, wallet_uuid: str):
    from .models import Wallet
    return db.query(Wallet).filter(
        Wallet.uuid == wallet_uuid
        ).with_for_update().first()