"""
Regression tests for #43: starting the same sleep type twice (double click,
retry, two tabs) must not create two simultaneously open sleep entries.
"""


def open_sleep_count(app, sleep_type):
    with app.app_context():
        from app.models.database import get_db
        row = get_db().execute(
            'SELECT COUNT(*) AS c FROM sleep WHERE end_time IS NULL AND type = ?',
            (sleep_type,)
        ).fetchone()
        return row['c']


def test_starting_night_sleep_twice_creates_only_one_open_entry(app, client):
    resp1 = client.post('/sleep/night/start', data={})
    resp2 = client.post('/sleep/night/start', data={})

    assert resp1.status_code < 400
    assert resp2.status_code < 400
    assert open_sleep_count(app, 'night') == 1


def test_starting_nap_twice_creates_only_one_open_entry(app, client):
    resp1 = client.post('/sleep/nap/start', data={})
    resp2 = client.post('/sleep/nap/start', data={})

    assert resp1.status_code < 400
    assert resp2.status_code < 400
    assert open_sleep_count(app, 'nap') == 1


def test_night_sleep_can_be_restarted_after_ending(app, client):
    client.post('/sleep/night/start', data={})
    client.post('/sleep/night/end', data={})
    client.post('/sleep/night/start', data={})

    assert open_sleep_count(app, 'night') == 1
