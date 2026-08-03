from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, current_app, g, jsonify, request
from flask_bcrypt import Bcrypt

from server.models import User, db

bcrypt = Bcrypt()
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or len(password) < 8:
        return jsonify({"error": "email and a password of at least 8 characters are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409
    user = User(
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "email": user.email}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if user is None or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid email or password"}), 401
    token = jwt.encode(
        {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc)
            + timedelta(hours=current_app.config["JWT_EXPIRY_HOURS"]),
        },
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return jsonify({"token": token})


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "missing bearer token"}), 401
        try:
            payload = jwt.decode(
                header[len("Bearer ") :],
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid or expired token"}), 401
        user = db.session.get(User, int(payload["sub"]))
        if user is None:
            return jsonify({"error": "invalid or expired token"}), 401
        g.user = user
        return fn(*args, **kwargs)

    return wrapper
