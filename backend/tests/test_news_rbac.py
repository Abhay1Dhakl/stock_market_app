def test_viewer_cannot_recategorize_news(client, viewer_user, seeded_company_data):
    login_response = client.post(
        "/api/auth/login",
        json={"email": viewer_user.email, "password": "viewer123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    article_id = seeded_company_data["article"].id
    company_id = seeded_company_data["company"].id
    response = client.post(
        f"/api/news/{article_id}/recategorize",
        json={"company_ids": [company_id], "notes": "Viewer should be blocked"},
        headers=headers,
    )
    assert response.status_code == 403
