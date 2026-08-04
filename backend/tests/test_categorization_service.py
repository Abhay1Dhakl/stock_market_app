from decimal import Decimal

from sqlalchemy import select

from app.models import Company, NewsArticle, NewsCompanyTag
from app.services.categorization_service import categorize_news_articles, list_review_queue_articles


def test_categorize_news_articles_creates_multi_label_system_tags(db_session, seeded_company_data):
    second_company = Company(
        symbol="SHIVM",
        name="Shivam Cements Limited",
        sector="Manufacturing And Processing",
        aliases=["Shivam", "Shivam Cements"],
        description="Cement company",
        is_active=True,
    )
    db_session.add(second_company)
    db_session.commit()
    db_session.refresh(second_company)

    article = NewsArticle(
        source_name="sharesansar",
        source_url="https://example.com/nabil-shivam-growth",
        headline="NABIL and Shivam report strong profit growth",
        excerpt="Both companies reported growth.",
        body_text="NABIL posted a profit surge while Shivam Cements Limited recorded strong growth in sales.",
        raw_payload={},
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)

    summary = categorize_news_articles(db_session, article_ids=[article.id], only_missing=False)
    refreshed_article = db_session.scalar(
        select(NewsArticle).where(NewsArticle.id == article.id)
    )
    tags = list(
        db_session.scalars(
            select(NewsCompanyTag)
            .where(NewsCompanyTag.news_article_id == article.id)
            .order_by(NewsCompanyTag.company_id.asc())
        ).all()
    )

    assert summary["processed"] == 1
    assert summary["tagged"] == 2
    assert refreshed_article is not None
    assert refreshed_article.sentiment_label == "positive"
    assert [tag.company.symbol for tag in tags] == ["NABIL", "SHIVM"]
    assert all(tag.tag_source == "system" for tag in tags)
    assert all(tag.confidence_score >= Decimal("0.65") for tag in tags)


def test_review_queue_includes_untagged_and_low_confidence_articles(db_session, seeded_company_data):
    low_confidence_article = NewsArticle(
        source_name="merolagani",
        source_url="https://example.com/ambiguous-article",
        headline="Banking discussion continues",
        excerpt="Possible mention of Nabil.",
        body_text="The article briefly mentioned Nabil once.",
        raw_payload={},
    )
    untagged_article = NewsArticle(
        source_name="sharesansar",
        source_url="https://example.com/no-match-article",
        headline="Macroeconomic overview",
        excerpt="No tracked company match.",
        body_text="This article contains no clear watchlist entity.",
        raw_payload={},
    )
    db_session.add_all([low_confidence_article, untagged_article])
    db_session.commit()
    db_session.refresh(low_confidence_article)
    db_session.refresh(untagged_article)

    db_session.add(
        NewsCompanyTag(
            news_article_id=low_confidence_article.id,
            company_id=seeded_company_data["company"].id,
            confidence_score=Decimal("0.4000"),
            tag_source="system",
            match_summary="Weak single mention",
        )
    )
    db_session.commit()

    queued_articles = list_review_queue_articles(db_session, limit=10)
    queued_ids = {article.id for article in queued_articles}

    assert low_confidence_article.id in queued_ids
    assert untagged_article.id in queued_ids
