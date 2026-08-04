def test_viewer_can_export_watchlist_summary_csv(client, viewer_user, seeded_company_data):
    login_response = client.post(
        "/api/auth/login",
        json={"email": viewer_user.email, "password": "viewer123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/reports/watchlist-summary.csv", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment;" in response.headers["content-disposition"]
    assert "symbol,name,sector" in response.text
    assert "NABIL,Nabil Bank Limited,Banking" in response.text
