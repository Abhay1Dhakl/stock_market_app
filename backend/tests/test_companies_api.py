from datetime import date
from decimal import Decimal

from app.models import FloorsheetTransaction


def test_companies_and_analysis_endpoints(client, db_session, seeded_company_data):
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

    db_session.add(
        FloorsheetTransaction(
            company_id=company_id,
            trading_date=date(2026, 8, 3),
            transaction_time=None,
            buyer_broker_code="58",
            seller_broker_code="42",
            quantity=1500,
            rate=Decimal("507.50"),
            amount=Decimal("761250.00"),
            row_hash="test-nabil-floorsheet-20260803-58-42-1500-50750",
            source_name="seed",
        )
    )
    db_session.commit()

    floorsheet_response = client.get(f"/api/companies/{company_id}/floorsheet", headers=headers)
    assert floorsheet_response.status_code == 200
    assert floorsheet_response.json()["date"] == "2026-08-03"
    assert floorsheet_response.json()["items"][0]["buyer_broker_code"] == "58"

    summary_response = client.get(f"/api/companies/{company_id}/behavior-summary", headers=headers)
    assert summary_response.status_code == 200
    assert summary_response.json()["pressure_indicator"] == "strong_buy_pressure"
