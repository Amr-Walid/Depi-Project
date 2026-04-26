"""
Tests for authentication endpoints.
Covers signup, login, token refresh, and profile access.
"""


class TestSignup:
    """Tests for POST /api/v1/auth/signup"""

    def test_signup_success(self, client):
        """Signup with valid email and password should return 201 with tokens."""
        response = client.post("/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "password": "securepassword123"
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_signup_duplicate_email(self, client, test_user):
        """Signup with an already registered email should return 400."""
        response = client.post("/api/v1/auth/signup", json={
            "email": test_user["email"],  # Already registered
            "password": "anotherpassword"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_signup_invalid_email(self, client):
        """Signup with an invalid email format should return 422."""
        response = client.post("/api/v1/auth/signup", json={
            "email": "not-an-email",
            "password": "securepassword123"
        })
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    def test_login_success(self, client, test_user):
        """Login with correct credentials should return 200 with tokens."""
        response = client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Login with wrong password should return 401."""
        response = client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": "wrongpassword",
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Login with a non-existent email should return 401."""
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "anypassword",
        })
        assert response.status_code == 401


class TestTokenRefresh:
    """Tests for POST /api/v1/auth/refresh"""

    def test_refresh_token_success(self, client, test_user):
        """Refreshing with a valid refresh token should return new tokens."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": test_user["refresh_token"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New tokens should be different from original
        assert data["refresh_token"] != test_user["refresh_token"]

    def test_refresh_token_reuse_after_rotation(self, client, test_user):
        """Using a refresh token that was already rotated should fail."""
        # First refresh — should succeed
        response1 = client.post("/api/v1/auth/refresh", json={
            "refresh_token": test_user["refresh_token"],
        })
        assert response1.status_code == 200

        # Second refresh with same token — should fail (it was revoked)
        response2 = client.post("/api/v1/auth/refresh", json={
            "refresh_token": test_user["refresh_token"],
        })
        assert response2.status_code == 401

    def test_refresh_with_invalid_token(self, client):
        """Refreshing with an invalid token string should return 401."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.string",
        })
        assert response.status_code == 401


class TestGetMe:
    """Tests for GET /api/v1/auth/me"""

    def test_get_me_authenticated(self, client, test_user, auth_headers):
        """Authenticated user should get their profile."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert "id" in data
        assert "created_at" in data
        assert "password_hash" not in data  # Must not leak password

    def test_get_me_no_token(self, client):
        """Accessing /me without a token should return 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Accessing /me with an invalid token should return 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401
