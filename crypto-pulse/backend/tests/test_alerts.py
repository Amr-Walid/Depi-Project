"""
Tests for price alert CRUD endpoints.
"""


class TestAlerts:
    """Tests for /api/v1/alerts endpoints"""

    def test_list_alerts_empty(self, client, auth_headers):
        """New user should have no alerts."""
        response = client.get("/api/v1/alerts", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_alert(self, client, auth_headers):
        """Should create a new price alert."""
        response = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTCUSDT", "condition": "above", "threshold": 70000.0},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["condition"] == "above"
        assert data["threshold"] == 70000.0
        assert data["is_active"] is True

    def test_create_alert_invalid_condition(self, client, auth_headers):
        """Should return 422 for invalid condition value."""
        response = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTCUSDT", "condition": "equals", "threshold": 70000.0},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_list_alerts_after_create(self, client, auth_headers):
        """Should list created alerts."""
        client.post(
            "/api/v1/alerts",
            json={"symbol": "BTCUSDT", "condition": "above", "threshold": 70000.0},
            headers=auth_headers,
        )
        client.post(
            "/api/v1/alerts",
            json={"symbol": "ETHUSDT", "condition": "below", "threshold": 3000.0},
            headers=auth_headers,
        )

        response = client.get("/api/v1/alerts", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_update_alert(self, client, auth_headers):
        """Should update an existing alert."""
        create_response = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTCUSDT", "condition": "above", "threshold": 70000.0},
            headers=auth_headers,
        )
        alert_id = create_response.json()["id"]

        # Update threshold and deactivate
        response = client.put(
            f"/api/v1/alerts/{alert_id}",
            json={"threshold": 75000.0, "is_active": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["threshold"] == 75000.0
        assert data["is_active"] is False
        assert data["symbol"] == "BTCUSDT"  # Unchanged

    def test_update_nonexistent_alert(self, client, auth_headers):
        """Should return 404 for non-existent alert."""
        response = client.put(
            "/api/v1/alerts/9999",
            json={"threshold": 75000.0},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_alert(self, client, auth_headers):
        """Should delete an alert."""
        create_response = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTCUSDT", "condition": "above", "threshold": 70000.0},
            headers=auth_headers,
        )
        alert_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        list_response = client.get("/api/v1/alerts", headers=auth_headers)
        assert list_response.json() == []

    def test_alerts_no_auth(self, client):
        """Should return 401 for all endpoints without authentication."""
        assert client.get("/api/v1/alerts").status_code == 401
        assert client.post("/api/v1/alerts", json={"symbol": "BTC", "condition": "above", "threshold": 1}).status_code == 401
