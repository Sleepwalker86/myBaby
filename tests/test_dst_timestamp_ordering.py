"""
Regression tests for #46: Zeitstempel werden als ISO-Strings mit Zeitzonen-Offset
(+01:00 im Winter, +02:00 im Sommer) gespeichert. Ein reiner lexikografischer
Stringvergleich zweier offset-behafteter Werte ist rund um eine Zeitumstellung nicht
mehr verlässlich sortierbar, weil der Offset-Wechsel die Zeichenreihenfolge verfälschen
kann, obwohl die tatsächliche (UTC-)Reihenfolge korrekt ist.

Konkretes Beispiel (Zeitumstellung Sommer->Winter, Nacht 24./25.10.2026):
  night_sleep_end = "2026-10-25T02:15:00+01:00"  (01:15 UTC)
  waking_start    = "2026-10-25T02:45:00+02:00"  (00:45 UTC, also VOR dem Schlafende)
Lexikografisch ist "02:45+02:00" > "02:15+01:00", obwohl 00:45 UTC < 01:15 UTC ist.
Ein naiver SQL-String-Vergleich schließt das Aufwachen fälschlich aus dem Zeitraum
des Nachtschlafs aus, was die Wachzeit- und damit die Schlafdauer-Berechnung verfälscht.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_BERLIN = ZoneInfo('Europe/Berlin')


def insert_night_waking(app, start_time, end_time=None):
    with app.app_context():
        from app.models.database import get_db
        db = get_db()
        db.execute(
            'INSERT INTO night_waking (start_time, end_time) VALUES (?, ?)',
            (start_time, end_time)
        )
        db.commit()


def test_waking_across_dst_fallback_is_not_dropped_by_string_ordering(app):
    # Nachtschlaf beginnt am Vorabend der Zeitumstellung (noch Sommerzeit) und endet
    # während der doppelt vorkommenden Stunde nach der Umstellung (schon Winterzeit).
    night_sleep_start = "2026-10-24T21:00:00+02:00"
    night_sleep_end = "2026-10-25T02:15:00+01:00"

    # Das Aufwachen liegt in absoluter Zeit VOR dem Schlafende (00:45 UTC < 01:15 UTC),
    # trägt aber noch den Sommerzeit-Offset, wodurch es lexikografisch GRÖSSER als
    # night_sleep_end erscheint.
    waking_start = "2026-10-25T02:45:00+02:00"
    waking_end = "2026-10-25T02:50:00+02:00"
    insert_night_waking(app, waking_start, waking_end)

    with app.app_context():
        from app.models.models import NightWaking

        wakings = NightWaking.get_wakings_for_night_sleep(night_sleep_start, night_sleep_end)
        assert len(wakings) == 1

        duration_hours = NightWaking.get_total_waking_duration(night_sleep_start, night_sleep_end)
        assert duration_hours == round(5 / 60, 2)  # 5 Minuten Aufwachzeit


def test_total_sleep_duration_accounts_for_waking_across_dst_fallback(app):
    night_sleep_start = "2026-10-24T21:00:00+02:00"
    night_sleep_end = "2026-10-25T02:15:00+01:00"
    waking_start = "2026-10-25T02:45:00+02:00"
    waking_end = "2026-10-25T02:50:00+02:00"
    insert_night_waking(app, waking_start, waking_end)

    with app.app_context():
        from app.models.models import NightWaking

        start_dt = datetime.fromisoformat(night_sleep_start)
        end_dt = datetime.fromisoformat(night_sleep_end)
        raw_duration_hours = (end_dt - start_dt).total_seconds() / 3600

        waking_hours = NightWaking.get_total_waking_duration(night_sleep_start, night_sleep_end)
        net_duration_hours = raw_duration_hours - waking_hours

        # Ohne den Fix würde die Wachzeit fälschlich als 0 berechnet (Aufwachen wird durch
        # den String-Vergleich ausgeschlossen), wodurch die Netto-Schlafdauer zu hoch wäre.
        assert waking_hours > 0
        assert net_duration_hours < raw_duration_hours


def test_normalize_form_datetime_produces_fixed_width_format():
    from app.form_datetime import normalize_form_datetime

    # Ohne explizite Sekunden/Mikrosekunden im Formularwert
    short = normalize_form_datetime("2026-10-25T02:15")
    # Ein anderer Zeitpunkt am selben Tag, der (vor dem Fix) durch abweichende
    # Mikrosekunden-Darstellung eine andere String-Länge hätte haben können
    other = normalize_form_datetime("2026-03-15T10:30")

    assert len(short) == len("2026-10-25T02:15:00+01:00")
    assert len(other) == len(short)
    assert "." not in short and "." not in other
