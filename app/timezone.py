"""Zentrale Quelle für die im gesamten Modul verwendete Zeitzone."""
import os
from datetime import datetime

import pytz


def get_app_timezone():
    """Gibt die konfigurierte Anwendungs-Zeitzone zurück (Standard: Europe/Berlin)."""
    tz_name = os.environ.get('APP_TIMEZONE', 'Europe/Berlin')
    return pytz.timezone(tz_name)


tz_berlin = get_app_timezone()


def to_berlin(value):
    """Parst einen ISO-Datetime-String oder ein datetime-Objekt und gibt es in der
    Anwendungs-Zeitzone zurück. Naive Werte werden als bereits lokale Zeit interpretiert.
    """
    if value is None:
        return None
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    else:
        dt = value

    if dt.tzinfo is None:
        return tz_berlin.localize(dt.replace(tzinfo=None))
    elif dt.tzinfo != tz_berlin:
        return dt.astimezone(tz_berlin)
    return dt
