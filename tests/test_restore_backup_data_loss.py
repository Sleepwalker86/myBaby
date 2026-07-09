"""
Regression tests for #42: Beim Wiederherstellen eines JSON-Backups wurde jede Tabelle
sofort per DELETE geleert, bevor geprueft wurde, ob das Backup fuer diese Tabelle
ueberhaupt Daten enthielt. Ein unvollstaendiges oder manipuliertes Backup konnte so
unwiderruflich vorhandene Daten loeschen. Restore muss jetzt (a) Backups mit komplett
fehlenden Tabellen-Schluesseln ablehnen, (b) bei leeren-aber-vorhandenen Schluesseln
eine explizite Zusatzbestaetigung verlangen, wenn dadurch aktuelle Daten verloren
gingen, und (c) vor jedem tatsaechlichen Restore automatisch einen Sicherungspunkt
der bisherigen Daten anlegen.
"""
import io
import json
import os

from app.routes.settings import BACKUP_TABLES


def insert_weight(app, timestamp, weight_kg=4.0):
    with app.app_context():
        from app.models.database import get_db
        db = get_db()
        cursor = db.execute(
            'INSERT INTO weight (timestamp, weight_kg) VALUES (?, ?)',
            (timestamp, weight_kg)
        )
        db.commit()
        return cursor.lastrowid


def count(app, table):
    with app.app_context():
        from app.models.database import get_db
        return get_db().execute(f'SELECT COUNT(*) AS c FROM {table}').fetchone()['c']


def full_backup_payload(overrides=None):
    payload = {'exported_at': '2026-07-01T10:00:00', 'version': 'v1.0.0'}
    for table in BACKUP_TABLES:
        payload[table] = []
    # baby_info hat durch die Migration immer einen Default-Eintrag, sonst wuerde
    # jeder Test ungewollt in den "Daten gehen verloren"-Zweig laufen.
    payload['baby_info'] = [{'id': 1, 'birth_date': '2026-01-01'}]
    if overrides:
        payload.update(overrides)
    return payload


def post_restore(client, payload, confirm_empty_tables=False):
    data = {
        'backup_file': (io.BytesIO(json.dumps(payload).encode('utf-8')), 'backup.json'),
        'confirm_restore': '1',
    }
    if confirm_empty_tables:
        data['confirm_empty_tables'] = '1'
    return client.post('/settings/restore', data=data, content_type='multipart/form-data')


def test_restore_rejects_backup_with_missing_table_keys(app, client):
    insert_weight(app, '2026-07-01T08:00:00+02:00')

    payload = full_backup_payload()
    del payload['weight']  # Schluessel fehlt komplett, nicht nur leer

    resp = post_restore(client, payload, confirm_empty_tables=True)

    assert resp.status_code == 302
    # Daten duerfen nicht angefasst worden sein
    assert count(app, 'weight') == 1


def test_restore_rejects_empty_table_without_extra_confirmation_when_data_would_be_lost(app, client):
    insert_weight(app, '2026-07-01T08:00:00+02:00')

    payload = full_backup_payload()  # weight ist [] (vorhanden, aber leer)

    resp = post_restore(client, payload, confirm_empty_tables=False)

    assert resp.status_code == 302
    # Ohne explizite Zusatzbestaetigung darf nichts geloescht worden sein
    assert count(app, 'weight') == 1


def test_restore_allows_empty_table_with_explicit_extra_confirmation(app, client):
    insert_weight(app, '2026-07-01T08:00:00+02:00')

    payload = full_backup_payload()

    resp = post_restore(client, payload, confirm_empty_tables=True)

    assert resp.status_code == 302
    assert count(app, 'weight') == 0


def test_restore_creates_automatic_restore_point_before_deleting_data(app, client):
    insert_weight(app, '2026-07-01T08:00:00+02:00')

    from app.models.database import get_database_path
    restore_points_dir = os.path.join(os.path.dirname(get_database_path()), 'restore_points')
    # Der Verzeichnispfad haengt nur vom (system-)Temp-Verzeichnis ab, nicht vom
    # eindeutigen DB-Dateinamen - andere Testlaeufe koennen dort bereits Dateien
    # hinterlassen haben, daher per Diff statt absoluter Anzahl pruefen.
    files_before = set(os.listdir(restore_points_dir)) if os.path.isdir(restore_points_dir) else set()

    payload = full_backup_payload()
    post_restore(client, payload, confirm_empty_tables=True)

    assert os.path.isdir(restore_points_dir)
    files_after = set(os.listdir(restore_points_dir))
    new_files = [f for f in (files_after - files_before) if f.startswith('pre_restore_')]
    assert len(new_files) == 1

    with open(os.path.join(restore_points_dir, new_files[0]), encoding='utf-8') as f:
        snapshot = json.load(f)
    # Der Sicherungspunkt enthaelt den Datensatz, der gleich geloescht wird
    assert len(snapshot['weight']) == 1


def test_restore_with_no_data_loss_does_not_require_extra_confirmation(app, client):
    payload = full_backup_payload(overrides={
        'weight': [{'timestamp': '2026-07-01T08:00:00+02:00', 'weight_kg': 4.2}],
    })

    resp = post_restore(client, payload, confirm_empty_tables=False)

    assert resp.status_code == 302
    assert count(app, 'weight') == 1
