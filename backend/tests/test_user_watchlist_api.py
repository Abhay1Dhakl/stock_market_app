def test_user_can_add_company_to_watchlist_and_read_behavior_summary(client, seeded_company_data):
    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    company_id = seeded_company_data["company"].id
    add_response = client.post(
        "/api/users/me/watchlist",
        json={"company_id": company_id},
        headers=headers,
    )
    assert add_response.status_code == 201
    assert add_response.json()["id"] == company_id

    watchlist_response = client.get("/api/users/me/watchlist", headers=headers)
    assert watchlist_response.status_code == 200
    assert watchlist_response.json()["items"][0]["company"]["symbol"] == "NABIL"

    telemetry_response = client.post(
        "/api/telemetry/events",
        json={"event_type": "company_view", "company_id": company_id, "page_path": "/companies/1"},
        headers=headers,
    )
    assert telemetry_response.status_code == 201

    behavior_response = client.get("/api/users/me/behavior-summary", headers=headers)
    assert behavior_response.status_code == 200
    assert behavior_response.json()["watchlist_size"] == 1
    assert behavior_response.json()["total_events"] >= 2


def test_admin_can_read_user_behavior_overview(client, seeded_company_data):
    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/api/users/me/watchlist",
        json={"company_id": seeded_company_data["company"].id},
        headers=headers,
    )

    overview_response = client.get("/api/admin/user-behavior", headers=headers)
    assert overview_response.status_code == 200
    assert overview_response.json()["items"][0]["email"] == "admin@example.com"
