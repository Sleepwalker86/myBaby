from flask import Blueprint, render_template, request
from app.models.models import get_all_entries_today, get_all_entries_date_range
from datetime import datetime, date, timedelta
import pytz
from app.i18n import get_language, _

tz_berlin = pytz.timezone('Europe/Berlin')

bp = Blueprint('entries', __name__, url_prefix='/entries')

@bp.app_template_filter('translate_entry_display')
def translate_entry_display(entry):
    """Übersetzt die display-Eigenschaft eines Eintrags basierend auf seiner Kategorie"""
    if not entry:
        return ""
    
    category = entry.get('category', '')
    
    if category == 'sleep':
        sleep_type = entry.get('type', '')
        if sleep_type == 'night':
            return _('entries.night_sleep')
        else:
            return _('entries.nap')
    elif category == 'night_waking':
        return _('entries.night_waking')
    elif category == 'feeding':
        side = entry.get('side', '').lower()
        if side == 'left' or side == 'links':
            return _('entries.feeding_left')
        else:
            return _('entries.feeding_right')
    elif category == 'bottle':
        amount = entry.get('amount', 0)
        return _('bottle.title') + f" ({amount} ml)"
    elif category == 'diaper':
        diaper_type = entry.get('type', '')
        if diaper_type == 'nass':
            return _('entries.diaper_wet')
        elif diaper_type == 'groß':
            return _('entries.diaper_solid')
        else:
            return _('entries.diaper_both')
    elif category == 'temperature':
        value = entry.get('value', 0)
        return _('entries.temperature') + f" ({value}°C)"
    elif category == 'medicine':
        name = entry.get('name', '')
        dose = entry.get('dose', '')
        return _('entries.medicine') + f" ({name}, {dose})"
    
    # Fallback: Original display verwenden
    return entry.get('display', '')

@bp.app_template_filter('format_datetime_de')
def format_datetime_de(value):
    """Formatiert einen ISO-Datetime-String ins deutsche Format DD.MM.YYYY HH:MM"""
    if not value:
        return ""
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = value
        
        # Konvertiere zu Berliner Zeitzone falls nötig
        if dt.tzinfo is None:
            # Keine Zeitzone - annehmen dass es bereits lokale Zeit ist
            dt = tz_berlin.localize(dt.replace(tzinfo=None))
        elif dt.tzinfo != tz_berlin:
            # Konvertiere zu Berliner Zeitzone
            dt = dt.astimezone(tz_berlin)
        
        # Entferne Zeitzone für Formatierung
        dt_local = dt.replace(tzinfo=None)
        return dt_local.strftime('%d.%m.%Y %H:%M')
    except (ValueError, AttributeError):
        return value

@bp.app_template_filter('calculate_duration')
def calculate_duration(start_time, end_time):
    """Berechnet die Dauer zwischen zwei Zeitstempeln und gibt sie als 'Xh Ym' zurück"""
    if not start_time or not end_time:
        return ""
    try:
        # Parse start_time
        if isinstance(start_time, str):
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = start_time
        
        # Parse end_time
        if isinstance(end_time, str):
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end_dt = end_time
        
        # Konvertiere zu Berliner Zeitzone falls nötig
        if start_dt.tzinfo is None:
            start_dt = tz_berlin.localize(start_dt.replace(tzinfo=None))
        elif start_dt.tzinfo != tz_berlin:
            start_dt = start_dt.astimezone(tz_berlin)
        
        if end_dt.tzinfo is None:
            end_dt = tz_berlin.localize(end_dt.replace(tzinfo=None))
        elif end_dt.tzinfo != tz_berlin:
            end_dt = end_dt.astimezone(tz_berlin)
        
        # Berechne Differenz
        duration = end_dt - start_dt
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 0:
            return ""
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return "< 1m"
    except (ValueError, AttributeError, TypeError):
        return ""

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
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = tz_berlin.localize(dt.replace(tzinfo=None))
                    elif dt.tzinfo != tz_berlin:
                        dt = dt.astimezone(tz_berlin)
                    return dt
                elif isinstance(time_str, datetime):
                    if time_str.tzinfo is None:
                        return tz_berlin.localize(time_str.replace(tzinfo=None))
                    elif time_str.tzinfo != tz_berlin:
                        return time_str.astimezone(tz_berlin)
                    return time_str
                return tz_berlin.localize(datetime(2000, 1, 1))
            except (ValueError, AttributeError):
                return tz_berlin.localize(datetime(2000, 1, 1))
        entries.sort(key=get_entry_time)
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
            if isinstance(ts_str, datetime):
                if ts_str.tzinfo is None:
                    return tz_berlin.localize(ts_str.replace(tzinfo=None))
                elif ts_str.tzinfo != tz_berlin:
                    return ts_str.astimezone(tz_berlin)
                return ts_str
            
            try:
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = tz_berlin.localize(dt.replace(tzinfo=None))
                elif dt.tzinfo != tz_berlin:
                    dt = dt.astimezone(tz_berlin)
                return dt
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
            elif isinstance(entry_day, datetime):
                # Konvertiere datetime zu date
                entry['day'] = entry_day.date()
        
        # Hilfsfunktion zum Extrahieren der Zeit für Sortierung
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
                elif isinstance(time_str, datetime):
                    if time_str.tzinfo is None:
                        return tz_berlin.localize(time_str.replace(tzinfo=None))
                    elif time_str.tzinfo != tz_berlin:
                        return time_str.astimezone(tz_berlin)
                    return time_str
                return tz_berlin.localize(datetime(2000, 1, 1))
            except (ValueError, AttributeError):
                return tz_berlin.localize(datetime(2000, 1, 1))
        
        # Sortiere zuerst nach Tag, dann nach timestamp
        all_entries.sort(key=lambda x: (
            x.get('day', date(2000, 1, 1)),
            get_entry_time(x)
        ))
        
        entries = all_entries
        date_display = f"{week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}"
    
    today = date.today()
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
                         weekday_names=weekday_names)

