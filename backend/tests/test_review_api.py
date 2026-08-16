from app.models import NewsArticle


def test_admin_can_fetch_review_queue(client, db_session):
    article = NewsArticle(
        source_name="merolagani",
        source_url="https://example.com/review-queue-item",
        headline="Uncategorized macro article",
        excerpt="Requires review.",
        body_text="No company was automatically matched yet.",
        raw_payload={},
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)

    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/news/review-queue?limit=10", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    returned_ids = {item["id"] for item in payload["items"]}
    assert article.id in returned_ids
