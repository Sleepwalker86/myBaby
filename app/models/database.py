import sqlite3
import os
from datetime import datetime
from flask import g

def get_db():
    """Holt die Datenbankverbindung aus dem Flask-Kontext"""
    if 'db' not in g:
        db_path = os.environ.get('DATABASE_PATH', '/data/baby_tracking.db')
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

def init_db():
    """Initialisiert die Datenbank mit allen Tabellen"""
    db = get_db()
    
    # Prüfe ob Tabellen bereits existieren
    cursor = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sleep'"
    )
    if cursor.fetchone():
        # Datenbank existiert bereits, keine Migrationen nötig
        return
    
    # Migrationen ausführen
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'migrations')
    if os.path.exists(migrations_dir):
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        
        for migration_file in migration_files:
            migration_path = os.path.join(migrations_dir, migration_file)
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql = f.read()
                db.executescript(sql)
        
        db.commit()

