import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from app.models.database import init_db, close_db
from app.models.models import BabyInfo
from app.i18n import _, get_language
from app.template_filters import register_template_filters

csrf = CSRFProtect()

def create_app():
    """Erstellt und konfiguriert die Flask-App"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['DATABASE'] = '/data/baby_tracking.db'
    csrf.init_app(app)

    # Strukturiertes Logging, damit Exceptions serverseitig nachvollziehbar sind,
    # ohne Details an den Client durchzureichen (Issue #49)
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        ))
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Gemeinsame Template-Filter einmalig registrieren (Issue #48)
    register_template_filters(app)

    # Datenbank initialisieren
    with app.app_context():
        init_db()
    
    # Teardown-Handler für Datenbankverbindung
    app.teardown_appcontext(close_db)
    
    # Context-Processor für global verfügbare Variablen
    @app.context_processor
    def inject_globals():
        """Macht globale Variablen in allen Templates verfügbar"""
        def translate(key, **kwargs):
            """Wrapper für die Übersetzungsfunktion, der im Request-Context funktioniert"""
            from app.i18n import translate as _translate
            return _translate(key, **kwargs)
        
        return {
            'baby_name': BabyInfo.get_name(),
            '_': translate,  # Übersetzungsfunktion für Jinja2
            'current_language': get_language()
        }
    
    # Routes registrieren
    from app.routes import main, sleep, feeding, bottle, porridge, diaper, temperature, medicine, illness, edit, trends, entries, settings, i18n, weight, height, head
    app.register_blueprint(main.bp)
    app.register_blueprint(sleep.bp)
    app.register_blueprint(feeding.bp)
    app.register_blueprint(bottle.bp)
    app.register_blueprint(porridge.bp)
    app.register_blueprint(diaper.bp)
    app.register_blueprint(temperature.bp)
    app.register_blueprint(medicine.bp)
    app.register_blueprint(illness.bp)
    app.register_blueprint(edit.bp)
    app.register_blueprint(trends.bp)
    app.register_blueprint(entries.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(i18n.bp)
    app.register_blueprint(weight.bp)
    app.register_blueprint(height.bp)
    app.register_blueprint(head.bp)
    
    return app

