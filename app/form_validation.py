"""
Hilfsfunktionen zum sicheren Parsen numerischer Formularfelder.

Python-`int`/`float` akzeptieren beliebig große Zahlen aus Nutzereingaben,
SQLite-Spalten (INTEGER/REAL) aber nicht. Ohne Obergrenzen-Prüfung *vor* dem
DB-Zugriff endet das in einem unbehandelten OverflowError statt einer
sauberen Fehlermeldung (siehe Issue #39).
"""
import math


def parse_bounded_number(raw_value, max_value, cast=float, min_value=0):
    """Parst raw_value mit `cast` und stellt sicher, dass min_value < Ergebnis <= max_value gilt.

    Wirft ValueError bei fehlender/ungültiger, nicht-endlicher (inf/NaN) oder
    außerhalb der Grenzen liegender Eingabe - auch in den Fällen, die sonst
    erst beim DB-Insert mit OverflowError scheitern würden.
    """
    try:
        parsed = cast(raw_value)
    except (ValueError, TypeError, OverflowError):
        raise ValueError(f'invalid numeric value: {raw_value!r}')
    if isinstance(parsed, float) and not math.isfinite(parsed):
        raise ValueError(f'invalid numeric value: {raw_value!r}')
    if parsed <= min_value or parsed > max_value:
        raise ValueError(f'value out of range: {parsed!r}')
    return parsed
