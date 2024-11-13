# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import logging

db = SQLAlchemy()   # Datenbank initialisieren
migrate = Migrate() # Migrations-Tool initialisieren

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialisiere Datenbank und Migration
    db.init_app(app)
    migrate.init_app(app, db)

    # Konfiguriere Logging
    logging.basicConfig(level=logging.DEBUG)

    # Modelle und Routen importieren, nachdem die App und DB initialisiert sind
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Fehlerhandler registrieren
    register_error_handlers(app)

    return app

def register_error_handlers(app):
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        # db.session.rollback()  # Optional: Rollback bei Datenbankfehlern
        return render_template('500.html'), 500
