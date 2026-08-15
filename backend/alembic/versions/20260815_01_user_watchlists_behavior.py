"""Add user watchlists, behavior events, and company coverage metadata."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260815_01"
down_revision: Union[str, None] = "20260804_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("source_kind", sa.String(length=20), server_default="seed", nullable=False))
    op.add_column("companies", sa.Column("coverage_status", sa.String(length=20), server_default="pending", nullable=False))
    op.add_column("companies", sa.Column("last_refresh_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("companies", sa.Column("last_refresh_error", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("created_by_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_companies_created_by_user_id_users",
        "companies",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "user_watchlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=20), server_default="manual", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name="fk_user_watchlists_company_id_companies", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_watchlists_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_user_watchlists"),
        sa.UniqueConstraint("user_id", "company_id", name="uq_user_watchlists_user_company"),
    )
    op.create_index("ix_user_watchlists_company_id", "user_watchlists", ["company_id"], unique=False)
    op.create_index("ix_user_watchlists_user_id", "user_watchlists", ["user_id"], unique=False)

    op.create_table(
        "user_behavior_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("page_path", sa.String(length=255), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["news_articles.id"], name="fk_user_behavior_events_article_id_news_articles", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name="fk_user_behavior_events_company_id_companies", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_behavior_events_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_user_behavior_events"),
    )
    op.create_index("ix_user_behavior_events_article_id", "user_behavior_events", ["article_id"], unique=False)
    op.create_index("ix_user_behavior_events_company_id", "user_behavior_events", ["company_id"], unique=False)
    op.create_index("ix_user_behavior_events_event_type", "user_behavior_events", ["event_type"], unique=False)
    op.create_index("ix_user_behavior_events_user_id", "user_behavior_events", ["user_id"], unique=False)

    op.alter_column("companies", "source_kind", server_default=None)
    op.alter_column("companies", "coverage_status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_user_behavior_events_user_id", table_name="user_behavior_events")
    op.drop_index("ix_user_behavior_events_event_type", table_name="user_behavior_events")
    op.drop_index("ix_user_behavior_events_company_id", table_name="user_behavior_events")
    op.drop_index("ix_user_behavior_events_article_id", table_name="user_behavior_events")
    op.drop_table("user_behavior_events")

    op.drop_index("ix_user_watchlists_user_id", table_name="user_watchlists")
    op.drop_index("ix_user_watchlists_company_id", table_name="user_watchlists")
    op.drop_table("user_watchlists")

    op.drop_constraint("fk_companies_created_by_user_id_users", "companies", type_="foreignkey")
    op.drop_column("companies", "created_by_user_id")
    op.drop_column("companies", "last_refresh_error")
    op.drop_column("companies", "last_refresh_at")
    op.drop_column("companies", "coverage_status")
    op.drop_column("companies", "source_kind")
