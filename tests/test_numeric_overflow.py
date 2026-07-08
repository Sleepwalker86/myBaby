"""
Regression tests for #39: absurdly large numeric form values must fail
cleanly (redirect + flash) instead of crashing with an unhandled
OverflowError when SQLite tries to bind a Python int/float that is too
large for an INTEGER/REAL column.
"""
import pytest

HUGE = '9' * 30


def last_id(app, table):
    with app.app_context():
        from app.models.database import get_db
        row = get_db().execute(f'SELECT id FROM {table} ORDER BY id DESC LIMIT 1').fetchone()
        return row['id']


@pytest.mark.parametrize('path,field', [
    ('/bottle/create', 'amount'),
    ('/porridge/create', 'amount'),
    ('/weight/create', 'weight_kg'),
    ('/height/create', 'height_cm'),
    ('/head/create', 'head_circumference_cm'),
    ('/temperature/create', 'value'),
])
def test_create_with_huge_value_does_not_500(client, path, field):
    resp = client.post(path, data={field: HUGE, 'timestamp': ''})
    assert resp.status_code < 500


@pytest.mark.parametrize('path,field', [
    ('/bottle/create', 'amount'),
    ('/porridge/create', 'amount'),
    ('/weight/create', 'weight_kg'),
    ('/height/create', 'height_cm'),
    ('/head/create', 'head_circumference_cm'),
    ('/temperature/create', 'value'),
])
def test_create_with_negative_huge_value_does_not_500(client, path, field):
    resp = client.post(path, data={field: f'-{HUGE}', 'timestamp': ''})
    assert resp.status_code < 500


def test_porridge_update_with_huge_value_does_not_500(app, client):
    client.post('/porridge/create', data={'amount': '100', 'timestamp': ''})
    porridge_id = last_id(app, 'porridge')

    resp = client.post(f'/porridge/update/{porridge_id}', data={'amount': HUGE, 'timestamp': ''})
    assert resp.status_code < 500


def test_edit_bottle_with_huge_value_does_not_500(app, client):
    client.post('/bottle/create', data={'amount': '100', 'timestamp': ''})
    bottle_id = last_id(app, 'bottle')

    resp = client.post(f'/edit/bottle/{bottle_id}', data={'amount': HUGE, 'timestamp': '2024-01-01T00:00'})
    assert resp.status_code < 500


def test_edit_porridge_with_huge_value_does_not_500(app, client):
    client.post('/porridge/create', data={'amount': '100', 'timestamp': ''})
    porridge_id = last_id(app, 'porridge')

    resp = client.post(f'/edit/porridge/{porridge_id}', data={'amount': HUGE, 'timestamp': '2024-01-01T00:00'})
    assert resp.status_code < 500


def test_edit_temperature_with_huge_value_does_not_500(app, client):
    client.post('/temperature/create', data={'value': '37.0'})
    temp_id = last_id(app, 'temperature')

    resp = client.post(f'/edit/temperature/{temp_id}', data={'value': HUGE, 'timestamp': '2024-01-01T00:00'})
    assert resp.status_code < 500


def test_bottle_create_still_accepts_valid_amount(app, client):
    resp = client.post('/bottle/create', data={'amount': '120', 'timestamp': ''})
    assert resp.status_code == 302
    with app.app_context():
        from app.models.database import get_db
        row = get_db().execute('SELECT amount FROM bottle ORDER BY id DESC LIMIT 1').fetchone()
        assert row['amount'] == 120


def test_bottle_create_rejects_amount_above_upper_bound(app, client):
    resp = client.post('/bottle/create', data={'amount': '5001', 'timestamp': ''})
    assert resp.status_code == 302
    with app.app_context():
        from app.models.database import get_db
        count = get_db().execute('SELECT COUNT(*) AS c FROM bottle').fetchone()['c']
        assert count == 0
