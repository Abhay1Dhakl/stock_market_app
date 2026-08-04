import os
from datetime import date
from decimal import Decimal
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_app.db"

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB_PATH}"
os.environ["ENVIRONMENT"] = "test"
os.environ["BOOTSTRAP_DEFAULT_ADMIN"] = "true"
os.environ["BOOTSTRAP_ADMIN_NAME"] = "Test Admin"
os.environ["BOOTSTRAP_ADMIN_EMAIL"] = "admin@example.com"
os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "admin123"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.main import app
from app.models import (
    Base,
    Company,
    CompanyAnalysisSnapshot,
    DailyPrice,
    NewsArticle,
    NewsCompanyTag,
    Role,
    User,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture()
def client(setup_database):
    with SessionLocal() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(client):
    with SessionLocal() as db:
        yield db


@pytest.fixture()
def viewer_user(db_session):
    viewer_role = db_session.scalar(select(Role).where(Role.name == "viewer"))
    viewer = User(
        full_name="Viewer User",
        email="viewer@example.com",
        password_hash=get_password_hash("viewer123"),
        role_id=viewer_role.id,
        is_active=True,
    )
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(viewer)
    return viewer


@pytest.fixture()
def analyst_user(db_session):
    analyst_role = db_session.scalar(select(Role).where(Role.name == "analyst"))
    analyst = User(
        full_name="Analyst User",
        email="analyst@example.com",
        password_hash=get_password_hash("analyst123"),
        role_id=analyst_role.id,
        is_active=True,
    )
    db_session.add(analyst)
    db_session.commit()
    db_session.refresh(analyst)
    return analyst


@pytest.fixture()
def seeded_company_data(db_session):
    company = Company(
        symbol="NABIL",
        name="Nabil Bank Limited",
        sector="Banking",
        aliases=["Nabil", "Nabil Bank"],
        description="Test banking company",
        is_active=True,
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)

    price = DailyPrice(
        company_id=company.id,
        trading_date=date(2026, 8, 3),
        open_price=Decimal("500.00"),
        high_price=Decimal("510.00"),
        low_price=Decimal("495.00"),
        close_price=Decimal("508.00"),
        volume=120000,
        turnover=Decimal("60960000.00"),
        source_name="seed",
    )
    snapshot = CompanyAnalysisSnapshot(
        company_id=company.id,
        trading_date=date(2026, 8, 3),
        close_price=Decimal("508.00"),
        vwap=Decimal("505.2500"),
        price_change_pct=Decimal("1.2000"),
        volume_change_pct=Decimal("4.3000"),
        pressure_indicator="strong_buy_pressure",
        is_volume_anomaly=False,
        anomaly_threshold=Decimal("150000.00"),
        news_count=2,
        news_sentiment_score=Decimal("0.6500"),
        next_day_price_change_pct=Decimal("0.5000"),
        next_day_volume_change_pct=Decimal("1.1000"),
        snapshot_payload={"window": "1d"},
    )
    article = NewsArticle(
        source_name="sharesansar",
        source_url="https://example.com/nabil-news",
        headline="Nabil reports quarterly growth",
        excerpt="Quarterly performance improved.",
        body_text="Nabil reported growth in quarterly earnings.",
        sentiment_label="positive",
        raw_payload={},
    )
    db_session.add_all([price, snapshot, article])
    db_session.commit()
    db_session.refresh(article)

    tag = NewsCompanyTag(
        news_article_id=article.id,
        company_id=company.id,
        confidence_score=Decimal("0.9000"),
        tag_source="system",
        match_summary="Matched symbol and alias",
    )
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)

    return {"company": company, "article": article}
