"""
Regression tests for a stale/nonexistent baby_id in POST /baby/<id>/update and
POST /baby/<id>/delete (found during review of Issue #33's multi-child support).

Both routes used to pass the baby_id straight into the model layer without checking
it still exists (unlike the sibling /baby/switch/<id> route, which does). A stale
form submission (e.g. a second browser tab, after the profile was already deleted
elsewhere) either silently created an unrelated new profile (update) or was reported
as a successful deletion despite doing nothing (delete).
"""


def all_baby_ids(app):
    with app.app_context():
        from app.models.models import BabyInfo
        return [b['id'] for b in BabyInfo.get_all_babies()]


def test_update_with_nonexistent_baby_id_does_not_create_a_new_profile(app, client):
    before = all_baby_ids(app)
    nonexistent_id = max(before) + 1000

    resp = client.post(f'/baby/{nonexistent_id}/update', data={
        'name': 'Geist',
        'birth_date': '2026-01-01',
        'gender': 'm',
    })

    assert resp.status_code == 302
    assert all_baby_ids(app) == before


def test_delete_with_nonexistent_baby_id_does_not_report_success(app, client):
    # Zweites Profil anlegen, damit delete_baby() nicht schon am "letztes Profil"-Guard scheitert
    client.post('/baby/create', data={'name': 'Zweitkind', 'birth_date': '2026-01-01'})
    before = all_baby_ids(app)
    nonexistent_id = max(before) + 1000

    resp = client.post(f'/baby/{nonexistent_id}/delete', data={}, follow_redirects=True)

    assert resp.status_code == 200
    assert all_baby_ids(app) == before
    assert 'Ungültige Eingabe'.encode('utf-8') in resp.data or b'invalid' in resp.data.lower()
