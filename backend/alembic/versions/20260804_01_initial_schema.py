"""Initial schema for stock market application."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260804_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=False)

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=25), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_companies"),
        sa.UniqueConstraint("symbol", name="uq_companies_symbol"),
    )
    op.create_index("ix_companies_symbol", "companies", ["symbol"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_users_role_id_roles", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "crawl_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_kind", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requested_sources", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("run_stats", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("run_kind in ('news', 'market_data', 'full')", name="ck_crawl_runs_run_kind"),
        sa.CheckConstraint("status in ('queued', 'running', 'succeeded', 'failed')", name="ck_crawl_runs_status"),
        sa.ForeignKeyConstraint(
            ["triggered_by_user_id"],
            ["users.id"],
            name="fk_crawl_runs_triggered_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_crawl_runs"),
    )
    op.create_index("ix_crawl_runs_status", "crawl_runs", ["status"], unique=False)

    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("headline", sa.String(length=500), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("crawled_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("sentiment_label", sa.String(length=32), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("crawl_run_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["crawl_run_id"], ["crawl_runs.id"], name="fk_news_articles_crawl_run_id_crawl_runs", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_news_articles"),
        sa.UniqueConstraint("source_url", name="uq_news_articles_source_url"),
    )
    op.create_index("ix_news_articles_published_at", "news_articles", ["published_at"], unique=False)
    op.create_index("ix_news_articles_source_name", "news_articles", ["source_name"], unique=False)

    op.create_table(
        "daily_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("open_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("high_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("low_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("close_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("turnover", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name="fk_daily_prices_company_id_companies", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_daily_prices"),
        sa.UniqueConstraint("company_id", "trading_date", name="uq_daily_prices_company_date"),
    )
    op.create_index("ix_daily_prices_company_id", "daily_prices", ["company_id"], unique=False)

    op.create_table(
        "floorsheet_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("transaction_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("buyer_broker_code", sa.String(length=32), nullable=False),
        sa.Column("seller_broker_code", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.BigInteger(), nullable=False),
        sa.Column("rate", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("row_hash", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name="fk_floorsheet_transactions_company_id_companies", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_floorsheet_transactions"),
        sa.UniqueConstraint("row_hash", name="uq_floorsheet_transactions_row_hash"),
    )
    op.create_index("ix_floorsheet_transactions_company_id", "floorsheet_transactions", ["company_id"], unique=False)
    op.create_index("ix_floorsheet_transactions_trading_date", "floorsheet_transactions", ["trading_date"], unique=False)

    op.create_table(
        "news_company_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("news_article_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("tag_source", sa.String(length=20), nullable=False),
        sa.Column("match_summary", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_news_company_tags_confidence_range"),
        sa.CheckConstraint("tag_source in ('system', 'manual')", name="ck_news_company_tags_tag_source"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name="fk_news_company_tags_company_id_companies", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_news_company_tags_created_by_user_id_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["news_article_id"], ["news_articles.id"], name="fk_news_company_tags_news_article_id_news_articles", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_news_company_tags"),
        sa.UniqueConstraint("news_article_id", "company_id", name="uq_news_company_tags_article_company"),
    )
    op.create_index("ix_news_company_tags_company_id", "news_company_tags", ["company_id"], unique=False)
    op.create_index("ix_news_company_tags_news_article_id", "news_company_tags", ["news_article_id"], unique=False)

    op.create_table(
        "news_tag_corrections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("news_article_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=False),
        sa.Column("previous_tags", sa.JSON(), nullable=False),
        sa.Column("updated_tags", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["news_article_id"], ["news_articles.id"], name="fk_news_tag_corrections_news_article_id_news_articles", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], name="fk_news_tag_corrections_reviewer_user_id_users", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_news_tag_corrections"),
    )
    op.create_index("ix_news_tag_corrections_news_article_id", "news_tag_corrections", ["news_article_id"], unique=False)

    op.create_table(
        "company_analysis_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("close_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("vwap", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("price_change_pct", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("volume_change_pct", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("pressure_indicator", sa.String(length=40), nullable=True),
        sa.Column("is_volume_anomaly", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("anomaly_threshold", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("news_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("news_sentiment_score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("next_day_price_change_pct", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("next_day_volume_change_pct", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("snapshot_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name="fk_company_analysis_snapshots_company_id_companies", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_company_analysis_snapshots"),
        sa.UniqueConstraint("company_id", "trading_date", name="uq_company_analysis_snapshots_company_date"),
    )
    op.create_index("ix_company_analysis_snapshots_company_id", "company_analysis_snapshots", ["company_id"], unique=False)

    role_table = sa.table(
        "roles",
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(
        role_table,
        [
            {
                "name": "admin",
                "description": "Manage watchlist, crawl runs, users, and roles.",
            },
            {
                "name": "analyst",
                "description": "Review categorizations, view dashboards, and export reports.",
            },
            {
                "name": "viewer",
                "description": "Read-only access to dashboards and reports.",
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_company_analysis_snapshots_company_id", table_name="company_analysis_snapshots")
    op.drop_table("company_analysis_snapshots")

    op.drop_index("ix_news_tag_corrections_news_article_id", table_name="news_tag_corrections")
    op.drop_table("news_tag_corrections")

    op.drop_index("ix_news_company_tags_news_article_id", table_name="news_company_tags")
    op.drop_index("ix_news_company_tags_company_id", table_name="news_company_tags")
    op.drop_table("news_company_tags")

    op.drop_index("ix_floorsheet_transactions_trading_date", table_name="floorsheet_transactions")
    op.drop_index("ix_floorsheet_transactions_company_id", table_name="floorsheet_transactions")
    op.drop_table("floorsheet_transactions")

    op.drop_index("ix_daily_prices_company_id", table_name="daily_prices")
    op.drop_table("daily_prices")

    op.drop_index("ix_news_articles_source_name", table_name="news_articles")
    op.drop_index("ix_news_articles_published_at", table_name="news_articles")
    op.drop_table("news_articles")

    op.drop_index("ix_crawl_runs_status", table_name="crawl_runs")
    op.drop_table("crawl_runs")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_companies_symbol", table_name="companies")
    op.drop_table("companies")

    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")

