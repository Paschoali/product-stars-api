import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from logging.handlers import RotatingFileHandler
from flask_caching import Cache
from datetime import date

db = SQLAlchemy()
cache = Cache()


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')

    db.init_app(app)
    cache.init_app(app)

    with app.app_context():
        from api.routes.cache import cache_bp
        from api.routes.login import login_bp
        from api.routes.person import person_bp
        from api.routes.errors import errors_bp

        db.create_all()

        app.register_blueprint(cache_bp, url_prefix='/cache')
        app.register_blueprint(login_bp, url_prefix='/login')
        app.register_blueprint(person_bp, url_prefix='/person')
        app.register_blueprint(errors_bp)

        app.cache = Cache(app)

        formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
        handler = RotatingFileHandler(f'logs/{date.today()}.log', maxBytes=10000, backupCount=1)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.DEBUG)

        return app
