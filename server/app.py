from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from server.config import Config
from server.models import db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    CORS(app)
    db.init_app(app)
    Migrate(app, db)
    from server.auth import auth_bp, bcrypt

    bcrypt.init_app(app)
    app.register_blueprint(auth_bp)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
