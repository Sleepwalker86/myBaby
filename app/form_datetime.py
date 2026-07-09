"""Hilfen für Zeiten aus HTML-Formularen (datetime-local vs. ISO mit Offset)."""
from datetime import datetime

from app.timezone import tz_berlin as TZ_BERLIN


def normalize_form_datetime(value):
    """
    Wandelt einen POST-Zeitstempel in einen ISO-String mit Europe/Berlin um (für DB/Anzeige).

    Akzeptiert: Browser-UTC (…Z), ISO mit Offset, oder naives Datum (wie bisher: Berlin-Wandzeit).
    Leere Werte -> None.
    """
    if value is None or not str(value).strip():
        return None
    s = str(value).strip().replace('Z', '+00:00')
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ_BERLIN)
    else:
        dt = dt.astimezone(TZ_BERLIN)
    # Issue #46: Mikrosekunden konsequent verwerfen, damit alle gespeicherten
    # Zeitstempel dieselbe feste Länge haben (sonst wäre ein lexikografischer
    # Stringvergleich schon durch die reine An-/Abwesenheit der Mikrosekunden
    # inkonsistent sortierbar, unabhängig von der Zeitumstellung).
    return dt.replace(microsecond=0).isoformat()


def is_end_before_start(start_time, end_time):
    """Prüft zeitzonen-bewusst, ob end_time vor oder gleich start_time liegt.

    Vergleicht echte datetime-Objekte statt Strings, damit ein Offset-Wechsel
    durch die Zeitumstellung (siehe Issue #46) keine falschen Ergebnisse liefert.
    Erwartet Strings mit Offset, wie sie normalize_form_datetime() liefert.
    """
    if not start_time or not end_time:
        return False
    start_dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(str(end_time).replace('Z', '+00:00'))
    return end_dt <= start_dt
