from flask import Blueprint, render_template, request
from app.models.models import get_all_entries_today
from datetime import datetime, date, timedelta
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

bp = Blueprint('entries', __name__, url_prefix='/entries')

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
        def get_entry_time(entry):
            """Hilfsfunktion zum Extrahieren der Zeit für Sortierung"""
            time_str = entry.get('timestamp') or entry.get('start_time', '2000-01-01T00:00:00')
            try:
                if isinstance(time_str, str):
                    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                return time_str
            except (ValueError, AttributeError):
                return datetime(2000, 1, 1)
        entries.sort(key=get_entry_time)
        date_display = selected_date.strftime('%d.%m.%Y')
        if selected_date == date.today():
            date_display = "Heute"
        elif selected_date == date.today() - timedelta(days=1):
            date_display = "Gestern"
        elif selected_date == date.today() - timedelta(days=2):
            date_display = "Vorgestern"
    else:  # week
        # Wochenansicht: Hole Einträge für die gesamte Woche
        days_since_monday = selected_date.weekday()
        week_start = selected_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        all_entries = []
        seen_entry_ids = set()  # Verhindere Duplikate
        
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            day_entries = get_all_entries_today(current_date)
            for entry in day_entries:
                entry_id = entry.get('id')
                
                # Überspringe wenn dieser Eintrag bereits verarbeitet wurde
                if entry_id and entry_id in seen_entry_ids:
                    continue
                
                # Bestimme zu welchem Tag der Eintrag gehört
                # Für Schlaf-Einträge: Wenn end_time vorhanden, gehört er zum Tag des end_time
                if entry.get('category') == 'sleep' and entry.get('end_time'):
                    try:
                        end_dt = datetime.fromisoformat(entry['end_time'].replace('Z', '+00:00'))
                        if end_dt.tzinfo is None:
                            end_dt = tz_berlin.localize(end_dt.replace(tzinfo=None))
                        elif end_dt.tzinfo != tz_berlin:
                            end_dt = end_dt.astimezone(tz_berlin)
                        entry_day = end_dt.date()
                    except (ValueError, AttributeError):
                        # Fallback: Tag aus start_time bestimmen
                        try:
                            start_dt = datetime.fromisoformat(entry.get('timestamp', '').replace('Z', '+00:00'))
                            if start_dt.tzinfo is None:
                                start_dt = tz_berlin.localize(start_dt.replace(tzinfo=None))
                            elif start_dt.tzinfo != tz_berlin:
                                start_dt = start_dt.astimezone(tz_berlin)
                            entry_day = start_dt.date()
                        except (ValueError, AttributeError):
                            entry_day = current_date
                else:
                    # Für andere Einträge: Tag aus timestamp bestimmen
                    try:
                        ts_str = entry.get('timestamp', '')
                        if ts_str:
                            ts_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts_dt.tzinfo is None:
                                ts_dt = tz_berlin.localize(ts_dt.replace(tzinfo=None))
                            elif ts_dt.tzinfo != tz_berlin:
                                ts_dt = ts_dt.astimezone(tz_berlin)
                            entry_day = ts_dt.date()
                        else:
                            entry_day = current_date
                    except (ValueError, AttributeError):
                        entry_day = current_date
                
                # Stelle sicher, dass entry_day ein date-Objekt ist und innerhalb der Woche liegt
                if week_start <= entry_day <= week_end:
                    # Stelle sicher, dass entry_day wirklich ein date-Objekt ist
                    if isinstance(entry_day, date):
                        entry['day'] = entry_day
                    else:
                        # Fallback: versuche es zu konvertieren
                        try:
                            entry['day'] = date.fromisoformat(str(entry_day)) if isinstance(entry_day, str) else entry_day
                        except (ValueError, AttributeError):
                            entry['day'] = current_date
                    all_entries.append(entry)
                    
                    # Markiere diesen Eintrag als verarbeitet
                    if entry_id:
                        seen_entry_ids.add(entry_id)
        
        # Sortiere nach Datum und Zeit (chronologisch, älteste zuerst)
        def get_entry_time(entry):
            """Hilfsfunktion zum Extrahieren der Zeit für Sortierung"""
            time_str = entry.get('timestamp') or entry.get('start_time', '2000-01-01T00:00:00')
            try:
                if isinstance(time_str, str):
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = tz_berlin.localize(dt.replace(tzinfo=None))
                    elif dt.tzinfo != tz_berlin:
                        dt = dt.astimezone(tz_berlin)
                    return dt
                return time_str
            except (ValueError, AttributeError):
                return datetime(2000, 1, 1, tzinfo=tz_berlin)
        
        # Stelle sicher, dass alle entry['day'] Werte date-Objekte sind
        for entry in all_entries:
            if 'day' not in entry or not isinstance(entry.get('day'), date):
                # Versuche den Tag aus dem timestamp zu extrahieren
                try:
                    ts_str = entry.get('timestamp', '')
                    if ts_str:
                        ts_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                        if ts_dt.tzinfo is None:
                            ts_dt = tz_berlin.localize(ts_dt.replace(tzinfo=None))
                        elif ts_dt.tzinfo != tz_berlin:
                            ts_dt = ts_dt.astimezone(tz_berlin)
                        entry['day'] = ts_dt.date()
                    else:
                        entry['day'] = date(2000, 1, 1)
                except (ValueError, AttributeError):
                    entry['day'] = date(2000, 1, 1)
        
        # Sortiere zuerst nach Tag, dann nach Zeit
        all_entries.sort(key=lambda x: (
            x.get('day', date(2000, 1, 1)),
            get_entry_time(x)
        ))
        
        entries = all_entries
        date_display = f"{week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}"
    
    today = date.today()
    # Wochentags-Mapping für deutsche Anzeige
    weekday_names = {
        0: 'Montag',
        1: 'Dienstag',
        2: 'Mittwoch',
        3: 'Donnerstag',
        4: 'Freitag',
        5: 'Samstag',
        6: 'Sonntag'
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
                         weekday_names=weekday_names)

