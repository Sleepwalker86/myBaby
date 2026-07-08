"""Zentrale Quelle für die im gesamten Modul verwendete Zeitzone."""
import os

import pytz


def get_app_timezone():
    """Gibt die konfigurierte Anwendungs-Zeitzone zurück (Standard: Europe/Berlin)."""
    tz_name = os.environ.get('APP_TIMEZONE', 'Europe/Berlin')
    return pytz.timezone(tz_name)


tz_berlin = get_app_timezone()
