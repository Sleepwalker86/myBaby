import sqlite3
import os
from datetime import datetime
from flask import g, session

def get_database_path():
    """Gibt den konfigurierten Pfad zur SQLite-Datenbankdatei zurück"""
    return os.environ.get('DATABASE_PATH', '/data/baby_tracking.db')

def get_db():
    """Holt die Datenbankverbindung aus dem Flask-Kontext"""
    if 'db' not in g:
        db_path = get_database_path()
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Schließt die Datenbankverbindung"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_active_baby_id():
    """Liefert die ID des aktuell ausgewählten Kind-Profils (Issue #33).

    Analog zu session['lang'] in app/i18n.py: die Auswahl liegt in der
    Session, wird aber pro Request in flask.g gecacht. Fällt auf das erste
    vorhandene Profil zurück, wenn die Session keine (mehr gültige) Auswahl
    enthält, z.B. bei Erstinstallationen oder nachdem das aktive Kind
    gelöscht wurde.
    """
    if 'active_baby_id' in g:
        return g.active_baby_id

    db = get_db()
    session_baby_id = session.get('active_baby_id')

    if session_baby_id is not None:
        row = db.execute('SELECT id FROM baby_info WHERE id = ?', (session_baby_id,)).fetchone()
        if row:
            g.active_baby_id = row['id']
            return g.active_baby_id

    row = db.execute('SELECT id FROM baby_info ORDER BY id LIMIT 1').fetchone()
    g.active_baby_id = row['id'] if row else 1
    return g.active_baby_id

def init_db():
    """Initialisiert die Datenbank mit allen Tabellen"""
    db = get_db()
    
    # Migrationen ausführen
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'migrations')
    if os.path.exists(migrations_dir):
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        
        for migration_file in migration_files:
            migration_path = os.path.join(migrations_dir, migration_file)
            try:
                with open(migration_path, 'r', encoding='utf-8') as f:
                    sql = f.read()
                    # Führe SQL aus
                    db.executescript(sql)
            except sqlite3.OperationalError as e:
                # Ignoriere Fehler wenn Tabelle bereits existiert
                error_msg = str(e).lower()
                if 'already exists' not in error_msg and 'duplicate column' not in error_msg:
                    # Für INSERT OR IGNORE Fehler ignorieren
                    if 'insert or ignore' not in sql.lower():
                        raise
        
        db.commit()
    
    # Stelle sicher, dass baby_info Tabelle existiert (für bestehende Datenbanken)
    try:
        db.execute('SELECT 1 FROM baby_info LIMIT 1')
    except sqlite3.OperationalError:
        # Tabelle existiert nicht, erstelle sie
        db.execute('''
            CREATE TABLE IF NOT EXISTS baby_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                birth_date TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        db.execute("INSERT OR IGNORE INTO baby_info (id, birth_date) VALUES (1, date('now', '-6 months'))")
        db.commit()

