"""
Regression tests for #51: Eine Endzeit vor der Startzeit wurde beim Bearbeiten
(und teils schon beim Anlegen) stillschweigend akzeptiert - nur die Dauer-Anzeige
blieb leer, ohne dass der Nutzer eine Fehlermeldung erhielt. Speichern mit
end_time <= start_time muss jetzt abgelehnt werden.
"""


def insert_sleep(app, start_time, end_time=None, sleep_type='nap'):
    with app.app_context():
        from app.models.database import get_db
        db = get_db()
        cursor = db.execute(
            'INSERT INTO sleep (type, start_time, end_time) VALUES (?, ?, ?)',
            (sleep_type, start_time, end_time)
        )
        db.commit()
        return cursor.lastrowid


def insert_night_waking(app, start_time, end_time=None):
    with app.app_context():
        from app.models.database import get_db
        db = get_db()
        cursor = db.execute(
            'INSERT INTO night_waking (start_time, end_time) VALUES (?, ?)',
            (start_time, end_time)
        )
        db.commit()
        return cursor.lastrowid


def insert_feeding(app, timestamp, side='links', end_time=None):
    with app.app_context():
        from app.models.database import get_db
        db = get_db()
        cursor = db.execute(
            'INSERT INTO feeding (timestamp, side, end_time) VALUES (?, ?, ?)',
            (timestamp, side, end_time)
        )
        db.commit()
        return cursor.lastrowid


def get_row(app, table, row_id):
    with app.app_context():
        from app.models.database import get_db
        row = get_db().execute(f'SELECT * FROM {table} WHERE id = ?', (row_id,)).fetchone()
        return dict(row) if row else None


def count(app, table):
    with app.app_context():
        from app.models.database import get_db
        return get_db().execute(f'SELECT COUNT(*) AS c FROM {table}').fetchone()['c']


def test_is_end_before_start_detects_reversed_times():
    from app.form_datetime import is_end_before_start

    assert is_end_before_start(
        "2026-07-08T20:00:00+02:00", "2026-07-08T19:00:00+02:00"
    ) is True


def test_is_end_before_start_allows_equal_or_missing_end():
    from app.form_datetime import is_end_before_start

    assert is_end_before_start("2026-07-08T20:00:00+02:00", "2026-07-08T20:00:00+02:00") is True
    assert is_end_before_start("2026-07-08T20:00:00+02:00", None) is False
    assert is_end_before_start(None, "2026-07-08T20:00:00+02:00") is False
    assert is_end_before_start(
        "2026-07-08T19:00:00+02:00", "2026-07-08T20:00:00+02:00"
    ) is False


def test_is_end_before_start_is_dst_aware():
    from app.form_datetime import is_end_before_start

    # Wie in #46: Offset-Wechsel darf einen reinen String-Vergleich nicht täuschen.
    start = "2026-10-25T02:15:00+01:00"  # 01:15 UTC
    end = "2026-10-25T02:45:00+02:00"  # 00:45 UTC, tatsächlich VOR start
    assert is_end_before_start(start, end) is True


def test_edit_sleep_with_end_before_start_is_rejected(app, client):
    sleep_id = insert_sleep(app, "2026-07-08T18:00:00+02:00", "2026-07-08T19:00:00+02:00")

    resp = client.post(f'/edit/sleep/{sleep_id}', data={
        'start_time': '2026-07-08T20:00',
        'end_time': '2026-07-08T19:00',
        'type': 'nap',
    })

    assert resp.status_code == 302
    row = get_row(app, 'sleep', sleep_id)
    # Unveränderte, ursprünglich gültige Werte - kein stilles Übernehmen der vertauschten Zeiten.
    assert row['start_time'] == "2026-07-08T18:00:00+02:00"
    assert row['end_time'] == "2026-07-08T19:00:00+02:00"


def test_edit_feeding_with_end_before_start_is_rejected(app, client):
    feeding_id = insert_feeding(app, "2026-07-08T18:00:00+02:00")

    resp = client.post(f'/edit/feeding/{feeding_id}', data={
        'timestamp': '2026-07-08T20:00',
        'side': 'links',
        'end_time': '2026-07-08T19:00',
    })

    assert resp.status_code == 302
    row = get_row(app, 'feeding', feeding_id)
    assert row['end_time'] is None


def test_edit_night_waking_with_end_before_start_is_rejected(app, client):
    waking_id = insert_night_waking(app, "2026-07-08T02:00:00+02:00")

    resp = client.post(f'/edit/night_waking/{waking_id}', data={
        'start_time': '2026-07-08T03:00',
        'end_time': '2026-07-08T02:30',
    })

    assert resp.status_code == 302
    row = get_row(app, 'night_waking', waking_id)
    assert row['end_time'] is None


def test_feeding_create_with_end_before_start_is_rejected(app, client):
    resp = client.post('/feeding/create', data={
        'side': 'links',
        'start_time': '2026-07-08T20:00',
        'end_time': '2026-07-08T19:00',
    })

    assert resp.status_code == 302
    assert count(app, 'feeding') == 0


def test_sleep_nap_end_before_start_is_rejected(app, client):
    client.post('/sleep/nap/start', data={'start_time': '2026-07-08T20:00'})

    resp = client.post('/sleep/nap/end', data={'end_time': '2026-07-08T19:00'})

    assert resp.status_code == 302
    with app.app_context():
        from app.models.models import Sleep
        active = Sleep.get_active_sleep_by_type('nap')
    assert active is not None
    assert active['end_time'] is None


def test_sleep_night_end_before_start_is_rejected(app, client):
    client.post('/sleep/night/start', data={'start_time': '2026-07-08T22:00'})

    resp = client.post('/sleep/night/end', data={'end_time': '2026-07-08T21:00'})

    assert resp.status_code == 302
    with app.app_context():
        from app.models.models import Sleep
        active = Sleep.get_active_sleep_by_type('night')
    assert active is not None
    assert active['end_time'] is None


def test_night_waking_end_before_start_is_rejected(app, client):
    client.post('/sleep/night_waking/start', data={'start_time': '2026-07-08T02:00'})

    resp = client.post('/sleep/night_waking/end', data={'end_time': '2026-07-08T01:30'})

    assert resp.status_code == 302
    with app.app_context():
        from app.models.models import NightWaking
        active = NightWaking.get_active()
    assert active is not None
    assert active['end_time'] is None
