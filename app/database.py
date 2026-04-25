import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DATABASE")

logger.info("INIT_DATABASE_ENGINE_START")
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"sslmode": "require"}
)

try:
    logger.info(f"DB_CONNECT_ATTEMPT_TO: {DATABASE_URL.split('@')[-1]}")
    with engine.connect() as connection:
        logger.info("DB_CONNECTION_ESTABLISHED_SUCCESS")
except Exception as e:
    logger.critical(f"DB_CONNECTION_FATAL_ERROR: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
logger.info("DB_BASE_MODEL_DECLARED")

def get_db():
    logger.info("DB_SESSION_REQUESTED")
    db = SessionLocal()
    logger.info("DB_SESSION_OPENED")
    try:
        yield db
    except Exception as e:
        logger.error(f"DB_SESSION_RUNTIME_ERROR: {e}")
        raise
    finally:
        db.close()
        logger.info("DB_SESSION_CLOSED_BY_FINALLY")