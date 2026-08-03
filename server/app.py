from flask import Flask
from flask_cors import CORS

from server.config import Config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    CORS(app)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
