"""
Regression tests for #47: die Zeitzone war 12+ mal identisch als
`pytz.timezone('Europe/Berlin')` dupliziert und nicht konfigurierbar.
`app/timezone.py` ist jetzt die einzige Stelle, die die aktive Zeitzone
definiert, und liest sie optional aus der Umgebungsvariable APP_TIMEZONE.
"""
import importlib
import os


def _reload_timezone_module():
    import app.timezone
    return importlib.reload(app.timezone)


def test_defaults_to_europe_berlin_without_env_var(monkeypatch):
    monkeypatch.delenv('APP_TIMEZONE', raising=False)
    tz_module = _reload_timezone_module()

    assert tz_module.get_app_timezone().zone == 'Europe/Berlin'
    assert tz_module.tz_berlin.zone == 'Europe/Berlin'


def test_respects_app_timezone_env_var(monkeypatch):
    monkeypatch.setenv('APP_TIMEZONE', 'Europe/Vienna')
    tz_module = _reload_timezone_module()

    assert tz_module.get_app_timezone().zone == 'Europe/Vienna'
    assert tz_module.tz_berlin.zone == 'Europe/Vienna'

    # Aufräumen, damit nachfolgende Tests wieder die Standard-Zeitzone sehen.
    monkeypatch.delenv('APP_TIMEZONE', raising=False)
    _reload_timezone_module()
