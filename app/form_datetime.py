"""Hilfen für Zeiten aus HTML-Formularen (datetime-local vs. ISO mit Offset)."""
from datetime import datetime

import pytz

TZ_BERLIN = pytz.timezone('Europe/Berlin')


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
        dt = TZ_BERLIN.localize(dt)
    else:
        dt = dt.astimezone(TZ_BERLIN)
    # Issue #46: Mikrosekunden konsequent verwerfen, damit alle gespeicherten
    # Zeitstempel dieselbe feste Länge haben (sonst wäre ein lexikografischer
    # Stringvergleich schon durch die reine An-/Abwesenheit der Mikrosekunden
    # inkonsistent sortierbar, unabhängig von der Zeitumstellung).
    return dt.replace(microsecond=0).isoformat()
