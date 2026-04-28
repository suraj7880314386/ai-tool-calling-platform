"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import random

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router
from app.core.database import init_db, SessionLocal
from app.core.models import SampleData, Product

# ─── Logging ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Seed Sample Data ─────────────────────────────────────

def seed_database():
    """Populate the database with sample data for the DB query tool."""
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(SampleData).count() > 0:
            logger.info("Database already seeded")
            return

        # Seed users
        users = [
            SampleData(name="Alice Johnson", email="alice@example.com", role="admin",
                       signup_date=datetime.utcnow() - timedelta(days=30), is_active=1),
            SampleData(name="Bob Smith", email="bob@example.com", role="user",
                       signup_date=datetime.utcnow() - timedelta(days=15), is_active=1),
            SampleData(name="Charlie Brown", email="charlie@example.com", role="moderator",
                       signup_date=datetime.utcnow() - timedelta(days=7), is_active=1),
            SampleData(name="Diana Prince", email="diana@example.com", role="admin",
                       signup_date=datetime.utcnow() - timedelta(days=3), is_active=1),
            SampleData(name="Eve Wilson", email="eve@example.com", role="user",
                       signup_date=datetime.utcnow() - timedelta(days=1), is_active=1),
            SampleData(name="Frank Miller", email="frank@example.com", role="user",
                       signup_date=datetime.utcnow() - timedelta(days=60), is_active=0),
            SampleData(name="Grace Lee", email="grace@example.com", role="user",
                       signup_date=datetime.utcnow() - timedelta(days=45), is_active=1),
            SampleData(name="Henry Chen", email="henry@example.com", role="moderator",
                       signup_date=datetime.utcnow() - timedelta(days=5), is_active=1),
            SampleData(name="Iris Patel", email="iris@example.com", role="user",
                       signup_date=datetime.utcnow() - timedelta(days=2), is_active=1),
            SampleData(name="Jack Taylor", email="jack@example.com", role="user",
                       signup_date=datetime.utcnow() - timedelta(days=90), is_active=0),
        ]
        db.add_all(users)

        # Seed products
        products = [
            Product(name="Wireless Headphones", category="electronics", price=79.99, stock=150),
            Product(name="Python Programming Book", category="books", price=34.99, stock=200),
            Product(name="Running Shoes", category="sports", price=129.99, stock=75),
            Product(name="Organic Green Tea", category="food", price=12.99, stock=500),
            Product(name="Cotton T-Shirt", category="clothing", price=19.99, stock=300),
            Product(name="Mechanical Keyboard", category="electronics", price=149.99, stock=50),
            Product(name="Data Science Handbook", category="books", price=44.99, stock=120),
            Product(name="Yoga Mat", category="sports", price=29.99, stock=200),
            Product(name="Dark Chocolate Bar", category="food", price=4.99, stock=1000),
            Product(name="Winter Jacket", category="clothing", price=89.99, stock=80),
            Product(name="USB-C Hub", category="electronics", price=39.99, stock=250),
            Product(name="AI Fundamentals Book", category="books", price=54.99, stock=90),
        ]
        db.add_all(products)

        db.commit()
        logger.info(f"Seeded database: {len(users)} users, {len(products)} products")

    except Exception as e:
        db.rollback()
        logger.error(f"Seed failed: {e}")
    finally:
        db.close()


# ─── Lifespan ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("  AI Agent Tool-Calling API Platform")
    logger.info("=" * 60)
    logger.info(f"  LLM:   {settings.llm_model}")
    logger.info(f"  Tools: 5 (search, calculator, database, wikipedia, weather)")
    logger.info(f"  DB:    {settings.database_url[:30]}...")
    logger.info(f"  Retry: max {settings.max_retries}, backoff {settings.retry_backoff_base}x")
    logger.info("=" * 60)

    # Initialize database
    init_db()
    seed_database()

    logger.info("Platform ready! Docs at /docs")
    logger.info("=" * 60)

    yield

    logger.info("Shutting down...")


# ─── App ──────────────────────────────────────────────────

app = FastAPI(
    title="AI Agent Tool-Calling API Platform",
    description=(
        "Production-ready LLM agent with tool-calling — web search, calculator, "
        "database query, Wikipedia, and weather. Built with LangChain + FastAPI."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "AI Agent Tool-Calling API Platform",
        "version": "1.0.0",
        "tools": ["web_search", "calculator", "database_query", "wikipedia", "weather"],
        "docs": "/docs",
        "health": "/api/v1/health",
    }
