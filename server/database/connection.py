"""
Database connection and session management for Smart Shamba
PostgreSQL with pgvector extension
"""

import os
import logging
from typing import AsyncGenerator
from sqlmodel import SQLModel, create_engine, Session, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Database configuration
# Support Render's auto-injected DATABASE_URL, or build from individual vars (local dev)
_render_url = os.getenv("DATABASE_URL")

if _render_url:
    # Render injects DATABASE_URL — use it directly
    # Render may use "postgres://" scheme; SQLAlchemy requires "postgresql://"
    if _render_url.startswith("postgres://"):
        _render_url = _render_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = _render_url
    ASYNC_DATABASE_URL = _render_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    logger.info("Using DATABASE_URL from environment (Render managed PostgreSQL)")
else:
    # Local development — build from individual POSTGRES_* vars
    DATABASE_NAME = os.getenv("POSTGRES_DB", "smart-shamba")
    DATABASE_USER = os.getenv("POSTGRES_USER", "geoffreyyogo")
    DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD", "och13ng")
    DATABASE_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DATABASE_PORT = os.getenv("POSTGRES_PORT", "5432")

    DATABASE_URL = (
        f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )
    ASYNC_DATABASE_URL = (
        f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )
    logger.info(f"Using local PostgreSQL: {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")

# Sync engine (for migrations and simple operations)
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() == "true",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Async engine (for FastAPI endpoints)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() == "true",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def get_sync_session() -> Session:
    """Get a synchronous database session"""
    with Session(engine) as session:
        return session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session (FastAPI dependency)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db():
    """Create all tables (sync, for startup/migrations)"""
    # Import all models so they register with SQLModel metadata
    from database.models import (  # noqa: F401
        Farmer, Farm, SensorReading, ModelOutput,
        AgKnowledge, GEECountyData, Alert, USSDSession,
        BloomEvent, ChatHistory, MessageTemplate,
        AgrovetProduct, AgrovetOrder, MarketplaceListing,
        MarketplaceBid, IoTDevice, CropImage,
    )
    SQLModel.metadata.create_all(engine)
    logger.info("✓ Database tables created/verified")

    # ---- TimescaleDB: convert sensor_readings to hypertable ----
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if TimescaleDB extension exists
            result = conn.execute(text(
                "SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'"
            )).fetchone()
            if result:
                # Check if already a hypertable
                ht = conn.execute(text(
                    "SELECT 1 FROM timescaledb_information.hypertables "
                    "WHERE hypertable_name = 'sensor_readings'"
                )).fetchone()
                if not ht:
                    # Drop PK if it exists (hypertable needs ts in PK or no PK)
                    conn.execute(text(
                        "ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS sensor_readings_pkey"
                    ))
                    conn.execute(text(
                        "ALTER TABLE sensor_readings ADD PRIMARY KEY (id, ts)"
                    ))
                    conn.execute(text(
                        "SELECT create_hypertable('sensor_readings', 'ts', migrate_data => true)"
                    ))
                    conn.execute(text(
                        "ALTER TABLE sensor_readings SET (timescaledb.compress, "
                        "timescaledb.compress_segmentby = 'farm_id,device_id')"
                    ))
                    conn.execute(text(
                        "SELECT add_compression_policy('sensor_readings', INTERVAL '30 days')"
                    ))
                    conn.commit()
                    logger.info("✓ sensor_readings converted to TimescaleDB hypertable with compression")
                else:
                    logger.info("✓ sensor_readings hypertable already exists")
            else:
                logger.info("⚠ TimescaleDB extension not installed – skipping hypertable setup")
    except Exception as e:
        logger.warning(f"TimescaleDB hypertable setup skipped: {e}")

    # ---- gee_county_data: regular PG table with B-tree indexes ----
    # Satellite observation data is low-frequency (daily/weekly per county),
    # so a standard PostgreSQL table with proper indexes is more appropriate
    # than a TimescaleDB hypertable.  Reserve TimescaleDB for high-frequency
    # IoT sensor data only (industry best practice).
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_gee_county_date "
                "ON gee_county_data (county, observation_date DESC)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_gee_subcounty_date "
                "ON gee_county_data (county, sub_county, observation_date DESC)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_gee_date "
                "ON gee_county_data (observation_date DESC)"
            ))
            conn.commit()
            logger.info("✓ gee_county_data B-tree indexes verified")
    except Exception as e:
        logger.warning(f"gee_county_data index setup skipped: {e}")


async def check_connection() -> bool:
    """Check if database is connected"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result is not None
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
