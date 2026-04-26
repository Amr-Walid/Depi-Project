"""
Tests for watchlist CRUD endpoints.
"""


class TestWatchlists:
    """Tests for /api/v1/watchlists endpoints"""

    def test_list_watchlists_empty(self, client, auth_headers):
        """New user should have empty watchlist."""
        response = client.get("/api/v1/watchlists", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_add_to_watchlist(self, client, auth_headers):
        """Should add a coin to the watchlist."""
        response = client.post(
            "/api/v1/watchlists",
            json={"symbol": "BTCUSDT"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert "id" in data
        assert "added_at" in data

    def test_add_duplicate_to_watchlist(self, client, auth_headers):
        """Should return 400 when adding a coin that's already in watchlist."""
        client.post("/api/v1/watchlists", json={"symbol": "BTCUSDT"}, headers=auth_headers)
        response = client.post(
            "/api/v1/watchlists",
            json={"symbol": "BTCUSDT"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_list_watchlists_after_add(self, client, auth_headers):
        """Should return added coins in the watchlist."""
        client.post("/api/v1/watchlists", json={"symbol": "BTCUSDT"}, headers=auth_headers)
        client.post("/api/v1/watchlists", json={"symbol": "ETHUSDT"}, headers=auth_headers)

        response = client.get("/api/v1/watchlists", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        symbols = [item["symbol"] for item in data]
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" in symbols

    def test_remove_from_watchlist(self, client, auth_headers):
        """Should remove a coin from the watchlist."""
        # Add first
        add_response = client.post(
            "/api/v1/watchlists",
            json={"symbol": "BTCUSDT"},
            headers=auth_headers,
        )
        item_id = add_response.json()["id"]

        # Delete
        response = client.delete(f"/api/v1/watchlists/{item_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        list_response = client.get("/api/v1/watchlists", headers=auth_headers)
        assert list_response.json() == []

    def test_remove_nonexistent_watchlist_item(self, client, auth_headers):
        """Should return 404 when removing a non-existent item."""
        response = client.delete("/api/v1/watchlists/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_watchlist_no_auth(self, client):
        """Should return 401 for all endpoints without authentication."""
        assert client.get("/api/v1/watchlists").status_code == 401
        assert client.post("/api/v1/watchlists", json={"symbol": "BTC"}).status_code == 401
        assert client.delete("/api/v1/watchlists/1").status_code == 401
