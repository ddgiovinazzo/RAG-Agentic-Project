import pytest

from server.app import create_app


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
            "JWT_EXPIRY_HOURS": 24,
        }
    )
    with app.app_context():
        from server.models import db

        db.create_all()
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    client.post("/api/auth/register", json={"email": "me@test.com", "password": "password123"})
    token = client.post(
        "/api/auth/login", json={"email": "me@test.com", "password": "password123"}
    ).get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
