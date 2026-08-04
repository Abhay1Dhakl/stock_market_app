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
