"""
Tests for coin data and market overview endpoints.
All data endpoints require JWT authentication.
"""


class TestListCoins:
    """Tests for GET /api/v1/coins"""

    def test_list_coins_authenticated(self, client, auth_headers):
        """Should return list of supported coins with valid token."""
        response = client.get("/api/v1/coins", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 20  # 20 supported coins
        # Check structure of first coin
        coin = data[0]
        assert "symbol" in coin
        assert "name" in coin
        assert "is_active" in coin
        assert coin["symbol"] == "BTCUSDT"

    def test_list_coins_no_auth(self, client):
        """Should return 401 without authentication."""
        response = client.get("/api/v1/coins")
        assert response.status_code == 401


class TestCoinSummary:
    """Tests for GET /api/v1/coins/{symbol}/summary"""

    def test_coin_summary_btc(self, client, auth_headers):
        """Should return daily summary for BTC."""
        response = client.get("/api/v1/coins/BTCUSDT/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert "trading_date" in data
        assert "day_open" in data
        assert "day_close" in data
        assert "day_high" in data
        assert "day_low" in data
        assert "total_volume" in data
        assert "avg_price" in data
        assert "price_change_pct" in data
        assert "tick_count" in data

    def test_coin_summary_case_insensitive(self, client, auth_headers):
        """Should handle lowercase symbol."""
        response = client.get("/api/v1/coins/btcusdt/summary", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["symbol"] == "BTCUSDT"

    def test_coin_summary_not_found(self, client, auth_headers):
        """Should return 404 for unsupported coin."""
        response = client.get("/api/v1/coins/FAKECOIN/summary", headers=auth_headers)
        assert response.status_code == 404

    def test_coin_summary_no_auth(self, client):
        """Should return 401 without authentication."""
        response = client.get("/api/v1/coins/BTCUSDT/summary")
        assert response.status_code == 401


class TestCoinPrices:
    """Tests for GET /api/v1/coins/{symbol}/prices"""

    def test_coin_prices_default(self, client, auth_headers):
        """Should return 30 days of price data by default."""
        response = client.get("/api/v1/coins/BTCUSDT/prices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["days"] == 30
        assert len(data["prices"]) == 30
        # Check OHLCV structure
        price = data["prices"][0]
        assert "timestamp" in price
        assert "open" in price
        assert "high" in price
        assert "low" in price
        assert "close" in price
        assert "volume" in price

    def test_coin_prices_custom_days(self, client, auth_headers):
        """Should respect the days query parameter."""
        response = client.get("/api/v1/coins/ETHUSDT/prices?days=7", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["days"] == 7
        assert len(data["prices"]) == 7

    def test_coin_prices_not_found(self, client, auth_headers):
        """Should return 404 for unsupported coin."""
        response = client.get("/api/v1/coins/FAKECOIN/prices", headers=auth_headers)
        assert response.status_code == 404

    def test_coin_prices_no_auth(self, client):
        """Should return 401 without authentication."""
        response = client.get("/api/v1/coins/BTCUSDT/prices")
        assert response.status_code == 401


class TestMarketOverview:
    """Tests for GET /api/v1/market/overview"""

    def test_market_overview(self, client, auth_headers):
        """Should return market-wide statistics."""
        response = client.get("/api/v1/market/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_market_cap" in data
        assert "total_volume_24h" in data
        assert "btc_dominance" in data
        assert "active_coins" in data
        assert "top_gainers" in data
        assert "top_losers" in data
        assert "last_updated" in data
        assert data["active_coins"] == 20
        assert len(data["top_gainers"]) == 5
        assert len(data["top_losers"]) == 5

    def test_market_overview_no_auth(self, client):
        """Should return 401 without authentication."""
        response = client.get("/api/v1/market/overview")
        assert response.status_code == 401
