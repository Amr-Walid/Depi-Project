"""
Tests for portfolio CRUD endpoints.
"""


class TestPortfolios:
    """Tests for /api/v1/portfolios endpoints"""

    def test_list_portfolio_empty(self, client, auth_headers):
        """New user should have empty portfolio."""
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_add_position(self, client, auth_headers):
        """Should add a new position to portfolio."""
        response = client.post(
            "/api/v1/portfolios",
            json={"symbol": "BTCUSDT", "quantity": 0.5, "avg_buy_price": 65000.0},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["quantity"] == 0.5
        assert data["avg_buy_price"] == 65000.0

    def test_list_portfolio_after_add(self, client, auth_headers):
        """Should list portfolio positions."""
        client.post(
            "/api/v1/portfolios",
            json={"symbol": "BTCUSDT", "quantity": 0.5, "avg_buy_price": 65000.0},
            headers=auth_headers,
        )
        client.post(
            "/api/v1/portfolios",
            json={"symbol": "ETHUSDT", "quantity": 5.0, "avg_buy_price": 3200.0},
            headers=auth_headers,
        )

        response = client.get("/api/v1/portfolios", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_update_position(self, client, auth_headers):
        """Should update a portfolio position."""
        create_response = client.post(
            "/api/v1/portfolios",
            json={"symbol": "BTCUSDT", "quantity": 0.5, "avg_buy_price": 65000.0},
            headers=auth_headers,
        )
        position_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/portfolios/{position_id}",
            json={"quantity": 1.0, "avg_buy_price": 67000.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 1.0
        assert data["avg_buy_price"] == 67000.0

    def test_update_position_partial(self, client, auth_headers):
        """Should allow partial updates (only quantity)."""
        create_response = client.post(
            "/api/v1/portfolios",
            json={"symbol": "BTCUSDT", "quantity": 0.5, "avg_buy_price": 65000.0},
            headers=auth_headers,
        )
        position_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/portfolios/{position_id}",
            json={"quantity": 2.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 2.0
        assert data["avg_buy_price"] == 65000.0  # Unchanged

    def test_update_nonexistent_position(self, client, auth_headers):
        """Should return 404 for non-existent position."""
        response = client.put(
            "/api/v1/portfolios/9999",
            json={"quantity": 1.0},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_position(self, client, auth_headers):
        """Should delete a portfolio position."""
        create_response = client.post(
            "/api/v1/portfolios",
            json={"symbol": "BTCUSDT", "quantity": 0.5, "avg_buy_price": 65000.0},
            headers=auth_headers,
        )
        position_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/portfolios/{position_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        list_response = client.get("/api/v1/portfolios", headers=auth_headers)
        assert list_response.json() == []

    def test_portfolios_no_auth(self, client):
        """Should return 401 for all endpoints without authentication."""
        assert client.get("/api/v1/portfolios").status_code == 401
        assert client.post("/api/v1/portfolios", json={"symbol": "BTC", "quantity": 1, "avg_buy_price": 1}).status_code == 401
