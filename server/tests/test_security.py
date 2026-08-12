import pytest
from server.limiter import RateLimiter, rate_limit


def test_rate_limiter_sliding_window():
    limiter = RateLimiter()
    key = "test_client"
    # Allow max 3 requests per 60s
    assert limiter.is_rate_limited(key, limit=3, window=60) is False
    assert limiter.is_rate_limited(key, limit=3, window=60) is False
    assert limiter.is_rate_limited(key, limit=3, window=60) is False
    # 4th request should be rate limited
    assert limiter.is_rate_limited(key, limit=3, window=60) is True


def test_rate_limit_endpoint_response(app, client):
    app.config["ENABLE_RATE_LIMIT"] = True
    for _ in range(10):
        client.post("/api/auth/register", json={"email": "rate@test.com", "password": "password123"})
    res = client.post("/api/auth/register", json={"email": "rate@test.com", "password": "password123"})
    assert res.status_code == 429
    assert "Too many requests" in res.get_json()["error"]
    app.config["ENABLE_RATE_LIMIT"] = False


def test_prompt_max_length_exceeded(client, auth_headers):
    # Create conversation
    res = client.post("/api/conversations", json={"title": "Test"}, headers=auth_headers)
    assert res.status_code == 201
    conv_id = res.get_json()["id"]

    # Send prompt that exceeds 1000 characters
    long_prompt = "A" * 1005
    res = client.post(
        f"/api/conversations/{conv_id}/messages",
        json={"content": long_prompt},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "exceeds maximum allowed length" in res.get_json()["error"]
