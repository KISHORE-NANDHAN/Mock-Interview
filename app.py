from flask import Flask, app
import logging
from logging.handlers import RotatingFileHandler

from config import Config

# ---------------- BLUEPRINT IMPORTS ----------------
from routes.auth import auth_bp
from routes.companies import companies_bp
from routes.exam import exam_bp
from routes.profile import profile_bp
from routes.misc import misc_bp
from routes.pdf_export import download_bp
from routes.proctor import proctor_bp




def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # --------------------
    # LOGGER SETUP (ADD HERE)
    # --------------------
    handler = RotatingFileHandler(
        "app.log",
        maxBytes=1_000_000,
        backupCount=3
    )

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logging.basicConfig(level=logging.WARNING)

    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

    app.logger.info("Flask app started")

    # ---------------- REGISTER BLUEPRINTS ----------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(misc_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(proctor_bp)

    @app.route("/test_model")
    def test_model():
        from services.technical_evaluator import model
        return "Model loaded"


    return app


# ---------------- RUN ----------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, use_reloader=False, threaded=True)

