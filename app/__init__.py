from flask import Flask
from app.models.database import init_db, close_db

def create_app():
    """Erstellt und konfiguriert die Flask-App"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['DATABASE'] = '/data/baby_tracking.db'
    
    # Datenbank initialisieren
    with app.app_context():
        init_db()
    
    # Teardown-Handler für Datenbankverbindung
    app.teardown_appcontext(close_db)
    
    # Routes registrieren
    from app.routes import main, sleep, feeding, bottle, diaper, temperature, medicine, edit, trends
    app.register_blueprint(main.bp)
    app.register_blueprint(sleep.bp)
    app.register_blueprint(feeding.bp)
    app.register_blueprint(bottle.bp)
    app.register_blueprint(diaper.bp)
    app.register_blueprint(temperature.bp)
    app.register_blueprint(medicine.bp)
    app.register_blueprint(edit.bp)
    app.register_blueprint(trends.bp)
    
    return app

