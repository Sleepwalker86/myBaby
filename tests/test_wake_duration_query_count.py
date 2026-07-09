"""
Regression tests for #45: die Wachzeit-Berechnung in get_all_entries_today() und
get_all_entries_date_range() darf nicht mehr pro Schlaf-Eintrag eine zusätzliche
SQL-Query auslösen (N+1-Query-Problem), und das Ergebnis muss unverändert bleiben.
"""
from datetime import date


def insert_sleep(app, sleep_type, start_time, end_time=None):
    with app.app_context():
        from app.models.database import get_db
        db = get_db()
        db.execute(
            'INSERT INTO sleep (type, start_time, end_time) VALUES (?, ?, ?)',
            (sleep_type, start_time, end_time)
        )
        db.commit()


def count_queries(app, func, *args, **kwargs):
    """Zählt die Anzahl der von sqlite3 ausgeführten SQL-Statements während func() läuft."""
    from app.models import database

    calls = {'n': 0}
    with app.test_request_context():
        db = database.get_db()

        def trace(statement):
            calls['n'] += 1

        db.set_trace_callback(trace)
        try:
            result = func(*args, **kwargs)
        finally:
            db.set_trace_callback(None)
    return calls['n'], result


def test_query_count_independent_of_sleep_entry_count(app):
    # 20 abgeschlossene Nickerchen an einem Tag anlegen
    day = "2026-01-15"
    for h in range(0, 20):
        insert_sleep(
            app, 'nap',
            f"{day}T{h:02d}:00:00",
            f"{day}T{h:02d}:10:00"
        )

    from app.models.models import get_all_entries_today

    n_queries, entries = count_queries(app, get_all_entries_today, day)

    assert len(entries) == 20
    # Konstante, kleine Anzahl an Queries (nicht proportional zu 20 Einträgen).
    # Vor dem Fix waren es 20+ zusätzliche Queries allein für die Wachzeit-Berechnung.
    assert n_queries < 20


def test_wake_duration_values_correct_for_today(app):
    day = "2026-01-16"
    insert_sleep(app, 'nap', f"{day}T08:00:00", f"{day}T09:00:00")
    insert_sleep(app, 'nap', f"{day}T11:30:00", f"{day}T12:00:00")

    from app.models.models import get_all_entries_today
    with app.test_request_context():
        entries = get_all_entries_today(day)

    entries_by_start = {e['timestamp']: e for e in entries if e['category'] == 'sleep'}

    assert entries_by_start[f"{day}T08:00:00"]['wake_duration'] is None
    assert entries_by_start[f"{day}T11:30:00"]['wake_duration'] == "2h 30m"


def test_query_count_independent_of_sleep_entry_count_for_date_range(app):
    for d in range(1, 8):
        day = f"2026-02-{d:02d}"
        for h in range(0, 4):
            insert_sleep(
                app, 'nap',
                f"{day}T{h*2:02d}:00:00",
                f"{day}T{h*2:02d}:20:00"
            )

    from app.models.models import get_all_entries_date_range

    n_queries, entries = count_queries(
        app, get_all_entries_date_range, "2026-02-01", "2026-02-07"
    )

    assert len(entries) >= 28
    assert n_queries < 15
