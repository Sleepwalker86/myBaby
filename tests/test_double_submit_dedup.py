"""
Regression tests for #44: doppeltes Absenden eines Create-Formulars (z. B. durch
Touch-Delay bei übermüdeten Eltern) darf nicht zu zwei identischen Datenbank-
Einträgen führen. Serverseitiger Schutz greift, wenn ein inhaltlich identischer
Eintrag innerhalb weniger Sekunden bereits existiert.
"""
import pytest


def count(app, table):
    with app.app_context():
        from app.models.database import get_db
        return get_db().execute(f'SELECT COUNT(*) AS c FROM {table}').fetchone()['c']


@pytest.mark.parametrize('path,data,table', [
    ('/diaper/create', {'type': 'nass'}, 'diaper'),
    ('/bottle/create', {'amount': '120'}, 'bottle'),
    ('/porridge/create', {'amount': '80', 'food': 'Karotte'}, 'porridge'),
    ('/temperature/create', {'value': '37.2'}, 'temperature'),
    ('/medicine/create', {'name': 'Paracetamol', 'dose': '5ml'}, 'medicine'),
    ('/feeding/create', {'side': 'links'}, 'feeding'),
])
def test_double_submit_creates_only_one_entry(app, client, path, data, table):
    resp1 = client.post(path, data=data)
    resp2 = client.post(path, data=data)
    assert resp1.status_code == 302
    assert resp2.status_code == 302
    assert count(app, table) == 1


def test_double_submit_sleep_nap_start_creates_only_one_entry(app, client):
    client.post('/sleep/nap/start', data={})
    client.post('/sleep/nap/start', data={})
    assert count(app, 'sleep') == 1


def test_double_submit_night_waking_start_creates_only_one_entry(app, client):
    client.post('/sleep/night_waking/start', data={})
    client.post('/sleep/night_waking/start', data={})
    assert count(app, 'night_waking') == 1


def test_distinct_entries_within_window_are_not_merged(app, client):
    client.post('/diaper/create', data={'type': 'nass'})
    client.post('/diaper/create', data={'type': 'groß'})
    assert count(app, 'diaper') == 2


def test_second_submit_still_redirects_successfully(client):
    resp1 = client.post('/bottle/create', data={'amount': '100'})
    resp2 = client.post('/bottle/create', data={'amount': '100'})
    assert resp1.status_code == 302
    assert resp2.status_code == 302
