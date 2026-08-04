def test_companies_and_analysis_endpoints(client, seeded_company_data):
    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    companies_response = client.get("/api/companies", headers=headers)
    assert companies_response.status_code == 200
    companies_payload = companies_response.json()
    assert companies_payload["items"][0]["symbol"] == "NABIL"

    company_id = seeded_company_data["company"].id
    prices_response = client.get(f"/api/companies/{company_id}/prices?range=30d", headers=headers)
    assert prices_response.status_code == 200
    assert prices_response.json()["items"][0]["close_price"] == "508.00"

    summary_response = client.get(f"/api/companies/{company_id}/behavior-summary", headers=headers)
    assert summary_response.status_code == 200
    assert summary_response.json()["pressure_indicator"] == "strong_buy_pressure"

