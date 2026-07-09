"""Zentrale Quelle für die im gesamten Modul verwendete Zeitzone."""
import os
from datetime import datetime
from datetime import timezone as _fixed_timezone
from zoneinfo import ZoneInfo


def get_app_timezone():
    """Gibt die konfigurierte Anwendungs-Zeitzone zurück (Standard: Europe/Berlin)."""
    tz_name = os.environ.get('APP_TIMEZONE', 'Europe/Berlin')
    return ZoneInfo(tz_name)


tz_berlin = get_app_timezone()


def normalize_to_berlin(dt):
    """Normalisiert ein datetime auf die Anwendungs-Zeitzone mit einem fixen Offset.

    Alle Aufrufer teilen dasselbe tz_berlin-Objekt. CPython vergleicht/subtrahiert
    zwei aware datetimes mit identischem tzinfo-Objekt über einen Fastpath, der
    den UTC-Offset ignoriert und stattdessen die naiven Wanduhrzeiten vergleicht.
    Rund um eine Zeitumstellung (wenn sich der Offset ändert, das tzinfo-Objekt
    aber gleich bleibt) liefert das falsche Ergebnisse - anders als bei pytz, das
    pro Offset ein eigenes tzinfo-Objekt verwendet. Ein pro Aufruf frisch über
    zoneinfo aufgelöster, danach fixer Offset umgeht diesen Fastpath zuverlässig.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz_berlin)
    elif dt.tzinfo != tz_berlin:
        dt = dt.astimezone(tz_berlin)
    return dt.replace(tzinfo=_fixed_timezone(dt.utcoffset()))


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

    return normalize_to_berlin(dt)
