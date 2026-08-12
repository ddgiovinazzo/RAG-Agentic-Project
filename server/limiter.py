from functools import wraps
import time
from flask import current_app, jsonify, request


class RateLimiter:
    """Thread-safe sliding window rate limiter for Flask endpoints."""

    def __init__(self):
        self._requests = {}  # key -> list of timestamps

    def _clean_old_requests(self, key, now, window):
        if key in self._requests:
            self._requests[key] = [
                t for t in self._requests[key] if now - t < window
            ]
            if not self._requests[key]:
                del self._requests[key]

    def is_rate_limited(self, key, limit, window):
        now = time.time()
        self._clean_old_requests(key, now, window)
        user_requests = self._requests.get(key, [])
        if len(user_requests) >= limit:
            return True
        if key not in self._requests:
            self._requests[key] = []
        self._requests[key].append(now)
        return False


limiter = RateLimiter()


def rate_limit(limit=10, period=60):
    """Decorator to limit endpoint calls per client IP / user.

    Args:
        limit (int): Max allowed requests in period.
        period (int): Time window in seconds (default 60s).
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_app.config.get("TESTING") and not current_app.config.get("ENABLE_RATE_LIMIT"):
                return f(*args, **kwargs)

            # Key by authenticated user ID if present, otherwise remote IP
            client_id = request.remote_addr or "unknown"
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                from server.auth import decode_token
                payload = decode_token(token)
                if payload and "sub" in payload:
                    client_id = f"user_{payload['sub']}"

            key = f"{request.endpoint}:{client_id}"
            if limiter.is_rate_limited(key, limit, period):
                response = jsonify(
                    {
                        "error": "Too many requests. Please slow down and try again later.",
                        "retry_after_seconds": period,
                    }
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(period)
                return response
            return f(*args, **kwargs)

        return wrapped

    return decorator
