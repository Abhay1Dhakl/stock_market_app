def test_admin_can_create_user_and_new_user_can_login(client):
    admin_login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    admin_token = admin_login_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    create_response = client.post(
        "/api/admin/users",
        json={
            "full_name": "Analyst User",
            "email": "analyst@example.com",
            "password": "analyst123",
            "role": "analyst",
            "is_active": True,
        },
        headers=admin_headers,
    )

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["email"] == "analyst@example.com"
    assert payload["role"] == "analyst"
    assert payload["is_active"] is True

    analyst_login_response = client.post(
        "/api/auth/login",
        json={"email": "analyst@example.com", "password": "analyst123"},
    )
    assert analyst_login_response.status_code == 200
    assert analyst_login_response.json()["user"]["role"] == "analyst"


def test_admin_cannot_create_duplicate_user_email(client):
    admin_login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    admin_token = admin_login_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    first_response = client.post(
        "/api/admin/users",
        json={
            "full_name": "Viewer User",
            "email": "viewer@example.com",
            "password": "viewer123",
            "role": "viewer",
            "is_active": True,
        },
        headers=admin_headers,
    )
    second_response = client.post(
        "/api/admin/users",
        json={
            "full_name": "Viewer User Duplicate",
            "email": "viewer@example.com",
            "password": "viewer123",
            "role": "viewer",
            "is_active": True,
        },
        headers=admin_headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_admin_can_manage_watchlist_companies(client):
    admin_login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    admin_token = admin_login_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    create_response = client.post(
        "/api/admin/companies",
        json={
            "symbol": "NICA",
            "name": "NIC Asia Bank Limited",
            "sector": "Banking",
            "aliases": ["NIC Asia", "NICA"],
            "description": "Tracked bank",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["symbol"] == "NICA"
    assert payload["is_active"] is True

    list_response = client.get("/api/admin/companies", headers=admin_headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["symbol"] == "NICA"

    update_response = client.patch(
        f"/api/admin/companies/{payload['id']}",
        json={"is_active": False, "aliases": ["NIC Asia Bank"]},
        headers=admin_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False
    assert update_response.json()["aliases"] == ["NIC Asia Bank"]
