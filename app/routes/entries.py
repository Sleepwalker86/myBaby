from flask import Blueprint, render_template, request
from app.models.models import get_all_entries_today, get_all_entries_date_range, BabyInfo
from datetime import datetime, date, timedelta
from app.i18n import get_language, _

from app.timezone import normalize_to_berlin, to_berlin

bp = Blueprint('entries', __name__, url_prefix='/entries')


def _get_entry_time(entry):
    """Hilfsfunktion zum Extrahieren der Zeit für Sortierung"""
    time_str = entry.get('timestamp') or entry.get('start_time', '2000-01-01T00:00:00')
    try:
        return to_berlin(time_str)
    except (ValueError, AttributeError):
        return normalize_to_berlin(datetime(2000, 1, 1))


@bp.route('/')
def entries():
    """Zeigt alle Einträge mit Tages- oder Wochenansicht"""
    # Hole Parameter aus URL
    view = request.args.get('view', 'day')  # 'day' oder 'week'
    selected_date_str = request.args.get('date', None)
    
    # Bestimme das ausgewählte Datum
    if selected_date_str:
        try:
            selected_date = date.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # Berechne vorheriges und nächstes Datum
    if view == 'day':
        prev_date = selected_date - timedelta(days=1)
        next_date = selected_date + timedelta(days=1)
    else:  # week
        # Berechne Wochenanfang (Montag)
        days_since_monday = selected_date.weekday()
        week_start = selected_date - timedelta(days=days_since_monday)
        prev_date = week_start - timedelta(days=7)
        next_date = week_start + timedelta(days=7)
    
    # Hole alle Einträge
    if view == 'day':
        # Tagesansicht: Hole Einträge für den ausgewählten Tag
        entries = get_all_entries_today(selected_date)
        # Sortiere chronologisch (älteste zuerst)
        entries.sort(key=_get_entry_time)
        date_display = selected_date.strftime('%d.%m.%Y')
        if selected_date == date.today():
            date_display = _('common.today')
        elif selected_date == date.today() - timedelta(days=1):
            date_display = _('common.yesterday')
        elif selected_date == date.today() - timedelta(days=2):
            date_display = _('common.day_before_yesterday')
    else:  # week
        # Wochenansicht: Hole Einträge für die gesamte Woche
        days_since_monday = selected_date.weekday()
        week_start = selected_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        # PERFORMANCE-OPTIMIERUNG: Hole alle Einträge in einem Batch statt 7x get_all_entries_today()
        # Dies reduziert DB-Queries von ~56 (7 Tage × 8 Queries) auf ~8 Queries
        all_entries_raw = get_all_entries_date_range(week_start, week_end)
        
        all_entries = []
        seen_entry_ids = set()  # Verhindere Duplikate
        
        # PERFORMANCE: Cached datetime parsing - parse einmal und cache das Ergebnis
        def parse_timestamp_cached(ts_str):
            """Parst einen Timestamp und cached das Ergebnis im Entry"""
            if not ts_str:
                return None
            try:
                return to_berlin(ts_str)
            except (ValueError, AttributeError):
                return None
        
        # Filtere und gruppiere Einträge nach Tag
        for entry in all_entries_raw:
            entry_id = entry.get('id')
            
            # Überspringe wenn dieser Eintrag bereits verarbeitet wurde
            if entry_id and entry_id in seen_entry_ids:
                continue
            
            # Bestimme zu welchem Tag der Eintrag gehört
            entry_day = None
            # Für Schlaf-Einträge mit end_time: Tag aus end_time
            if entry.get('category') == 'sleep' and entry.get('end_time'):
                end_dt = parse_timestamp_cached(entry['end_time'])
                if end_dt:
                    entry_day = end_dt.date()
            
            # Für alle anderen Einträge: Tag aus timestamp
            if entry_day is None:
                ts_dt = parse_timestamp_cached(entry.get('timestamp', ''))
                if ts_dt:
                    entry_day = ts_dt.date()
                else:
                    # Fallback: verwende week_start
                    entry_day = week_start
            
            # Stelle sicher, dass entry_day ein date-Objekt ist (nicht datetime)
            if isinstance(entry_day, datetime):
                entry_day = entry_day.date()
            elif not isinstance(entry_day, date):
                try:
                    entry_day = date.fromisoformat(str(entry_day))
                except (ValueError, AttributeError):
                    entry_day = week_start
            
            # Setze entry.day explizit als date-Objekt
            entry['day'] = entry_day
            
            # Nur Einträge innerhalb der Woche hinzufügen
            if entry_day and week_start <= entry_day <= week_end:
                all_entries.append(entry)
                if entry_id:
                    seen_entry_ids.add(entry_id)
        
        # Stelle sicher, dass alle entry['day'] Werte date-Objekte sind (BEVOR sortiert wird)
        for entry in all_entries:
            entry_day = entry.get('day')
            if entry_day is None or not isinstance(entry_day, date):
                # Fallback: Tag aus timestamp extrahieren
                try:
                    ts_str = entry.get('timestamp', '')
                    if ts_str:
                        entry['day'] = to_berlin(ts_str).date()
                    else:
                        entry['day'] = date(2000, 1, 1)
                except (ValueError, AttributeError):
                    entry['day'] = date(2000, 1, 1)
            elif isinstance(entry_day, datetime):
                # Konvertiere datetime zu date
                entry['day'] = entry_day.date()
        
        # Sortiere zuerst nach Tag, dann nach timestamp
        all_entries.sort(key=lambda x: (
            x.get('day', date(2000, 1, 1)),
            _get_entry_time(x)
        ))
        
        entries = all_entries
        date_display = f"{week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}"
    
    today = date.today()
    sleep_meta = BabyInfo.get_sleep_meta_settings()
    # Wochentags-Mapping basierend auf aktueller Sprache
    lang = get_language()
    weekday_names = {
        0: _('common.weekday_monday', lang=lang),
        1: _('common.weekday_tuesday', lang=lang),
        2: _('common.weekday_wednesday', lang=lang),
        3: _('common.weekday_thursday', lang=lang),
        4: _('common.weekday_friday', lang=lang),
        5: _('common.weekday_saturday', lang=lang),
        6: _('common.weekday_sunday', lang=lang)
    }
    
    return render_template('entries.html',
                         entries=entries,
                         selected_date=selected_date,
                         prev_date=prev_date,
                         next_date=next_date,
                         view=view,
                         date_display=date_display,
                         today=today,
                         timedelta=timedelta,
                         weekday_names=weekday_names,
                         sleep_meta=sleep_meta)

