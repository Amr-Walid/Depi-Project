"""
Tests for the market sentiment endpoint.
"""


EXPECTED_SENTIMENT_KEYS = {
    "overall_score",
    "overall_label",
    "positive_pct",
    "negative_pct",
    "neutral_pct",
    "article_count",
    "last_updated",
}


class TestMarketSentiment:
    """Tests for GET /api/v1/market/sentiment"""

    def test_market_sentiment_authenticated(self, client, auth_headers):
        """Should return sentiment overview with valid authentication."""
        response = client.get("/api/v1/market/sentiment", headers=auth_headers)

        assert response.status_code == 200

    def test_market_sentiment_response_keys(self, client, auth_headers):
        """Should include all required sentiment response keys."""
        response = client.get("/api/v1/market/sentiment", headers=auth_headers)

        assert response.status_code == 200
        assert EXPECTED_SENTIMENT_KEYS.issubset(response.json().keys())

    def test_market_sentiment_missing_tables_returns_neutral(self, client, auth_headers):
        """Should return a safe neutral response when sentiment tables do not exist."""
        response = client.get("/api/v1/market/sentiment", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 0.0
        assert data["overall_label"] == "Neutral"
        assert data["positive_pct"] == 0.0
        assert data["negative_pct"] == 0.0
        assert data["neutral_pct"] == 0.0
        assert data["article_count"] == 0
        assert data["last_updated"] is None
        assert data["status"] == "sentiment_data_not_ready"
