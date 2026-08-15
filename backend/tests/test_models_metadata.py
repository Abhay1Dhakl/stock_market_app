from app.models import Base


def test_metadata_contains_core_tables() -> None:
    expected_tables = {
        "roles",
        "users",
        "user_watchlists",
        "user_behavior_events",
        "companies",
        "crawl_runs",
        "news_articles",
        "news_company_tags",
        "news_tag_corrections",
        "daily_prices",
        "floorsheet_transactions",
        "company_analysis_snapshots",
    }

    assert expected_tables.issubset(set(Base.metadata.tables.keys()))
