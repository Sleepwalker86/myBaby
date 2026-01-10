from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import (
    Sleep, Feeding, Bottle, Diaper, get_all_entries_today, BabyInfo
)
from app.models.database import get_db
from datetime import datetime, date, timedelta
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

bp = Blueprint('main', __name__)

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

def format_time_ago(timestamp):
    """Formatiert eine Zeitstempel als 'vor X Stunden/Minuten'"""
    if not timestamp:
        return "Noch nie"
    
    try:
        if isinstance(timestamp, str):
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            ts = timestamp
        
        now = datetime.now(tz_berlin)
        # Stelle sicher, dass ts auch eine Zeitzone hat
        if ts.tzinfo is None:
            # Wenn keine Zeitzone, annehmen dass es bereits lokale Zeit ist
            ts = tz_berlin.localize(ts.replace(tzinfo=None))
        elif ts.tzinfo != tz_berlin:
            # Konvertiere zu Berliner Zeitzone
            ts = ts.astimezone(tz_berlin)
        diff = now - ts
        
        if diff.total_seconds() < 0:
            return "Gerade eben"
        
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        
        if hours > 0:
            if minutes > 0:
                return f"vor {hours}h {minutes}m"
            return f"vor {hours}h"
        elif minutes > 0:
            return f"vor {minutes}m"
        else:
            return "Gerade eben"
    except (ValueError, AttributeError):
        return "Unbekannt"

def format_duration_hours(hours):
    """Formatiert Stunden als 'Xh Ym'"""
    if hours is None or hours == 0:
        return "0h"
    
    try:
        hours_float = float(hours)
        hours_int = int(hours_float)
        minutes = int((hours_float - hours_int) * 60)
        
        if hours_int > 0:
            if minutes > 0:
                return f"{hours_int}h {minutes}m"
            return f"{hours_int}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return "0h"
    except (ValueError, TypeError):
        return "0h"

@bp.route('/')
def index():
    """Hauptseite mit Tagesübersicht"""
    # Datum aus Request (Standard: heute)
    selected_date_str = request.args.get('date', date.today().isoformat())
    try:
        selected_date = date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = date.today()
    
    # Vorheriger und nächster Tag
    prev_date = (selected_date - timedelta(days=1)).isoformat()
    next_date = (selected_date + timedelta(days=1)).isoformat()
    is_today = selected_date == date.today()
    
    # Aktueller Schlafstatus (nur für heute relevant)
    active_sleep = Sleep.get_active_sleep() if is_today else None
    sleep_status = "schläft" if active_sleep else "wach"
    
    # Schlafdauer für den ausgewählten Tag
    sleep_duration_hours = Sleep.get_today_sleep_duration(selected_date)
    sleep_duration = format_duration_hours(sleep_duration_hours)
    
    # Zeit seit letztem Aufwachen oder seit Schlafbeginn (nur für heute)
    awake_since = None
    sleep_since = None
    if is_today:
        if active_sleep:
            # Baby schläft - berechne Zeit seit Schlafbeginn
            sleep_since = format_time_ago(active_sleep['start_time'])
        else:
            # Baby ist wach - berechne Zeit seit letztem Aufwachen
            db = get_db()
            last_sleep = db.execute(
                'SELECT end_time FROM sleep WHERE end_time IS NOT NULL ORDER BY end_time DESC LIMIT 1'
            ).fetchone()
            if last_sleep:
                awake_since = format_time_ago(last_sleep['end_time'])
            else:
                awake_since = "Heute"
    else:
        awake_since = None
        sleep_since = None
    
    # Letztes Stillen (nur für heute)
    if is_today:
        latest_feeding = Feeding.get_latest()
        feeding_ago = format_time_ago(latest_feeding['timestamp'] if latest_feeding else None)
    else:
        feeding_ago = None
    
    # Letzte Windel (nur für heute)
    if is_today:
        latest_diaper = Diaper.get_latest()
        diaper_ago = format_time_ago(latest_diaper['timestamp'] if latest_diaper else None)
    else:
        diaper_ago = None
    
    # Alle Einträge des ausgewählten Tages
    entries = get_all_entries_today(selected_date)
    
    # Berechne Timeline für Kreisdiagramm (für alle Tage)
    # Vollständiger 24-Stunden-Kreis
    wake_up_time_str = None
    timeline_events = []
    # Timeline-Events werden immer berechnet, auch wenn Baby schläft
    # Hole alle Einträge des Tages
    for entry in entries:
        # Für Schlaf-Einträge: Unterscheide zwischen Nachtschlaf und Nickerchen
        if entry.get('category') == 'sleep':
            start_time_str = entry.get('timestamp') or entry.get('start_time')
            end_time_str = entry.get('end_time')
            sleep_type = entry.get('type', 'night')
            
            if not start_time_str or not end_time_str:
                continue
            
            try:
                # Parse Start- und Endzeit
                if isinstance(start_time_str, str):
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                else:
                    start_time = start_time_str
                
                if isinstance(end_time_str, str):
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                else:
                    end_time = end_time_str
                
                if start_time.tzinfo is None:
                    start_time = tz_berlin.localize(start_time.replace(tzinfo=None))
                elif start_time.tzinfo != tz_berlin:
                    start_time = start_time.astimezone(tz_berlin)
                
                if end_time.tzinfo is None:
                    end_time = tz_berlin.localize(end_time.replace(tzinfo=None))
                elif end_time.tzinfo != tz_berlin:
                    end_time = end_time.astimezone(tz_berlin)
                
                # Prüfe ob Start oder Ende am ausgewählten Tag liegt
                start_date = start_time.date()
                end_date = end_time.date()
                
                if start_date == selected_date or end_date == selected_date:
                    # Berechne Stunden und Minuten für Start und Ende
                    start_hour = start_time.hour
                    start_minute = start_time.minute
                    end_hour = end_time.hour
                    end_minute = end_time.minute
                    
                    if sleep_type == 'night':
                        # Nachtschlaf: Nur Einschlafen anzeigen, wenn es heute ist (nicht vom Vortag)
                        if start_date == selected_date:
                            timeline_events.append({
                                'category': 'sleep',
                                'type': 'night',
                                'event_type': 'sleep_start',  # Einschlafen
                                'time_str': start_time.strftime('%H:%M'),
                                'hour': start_hour,
                                'minute': start_minute
                            })
                        
                        # Aufwachzeit nur anzeigen, wenn es heute ist
                        if end_date == selected_date:
                            timeline_events.append({
                                'category': 'sleep',
                                'type': 'night',
                                'event_type': 'sleep_end',  # Aufwachen
                                'time_str': end_time.strftime('%H:%M'),
                                'hour': end_hour,
                                'minute': end_minute
                            })
                    else:
                        # Nickerchen: Bogen zwischen Start und Ende
                        timeline_events.append({
                            'category': entry.get('category', ''),
                            'type': entry.get('type', ''),
                            'display': entry.get('display', ''),
                            'start_time': start_time.strftime('%H:%M'),
                            'end_time': end_time.strftime('%H:%M'),
                            'start_hour': start_hour,
                            'start_minute': start_minute,
                            'end_hour': end_hour,
                            'end_minute': end_minute
                        })
            except (ValueError, AttributeError):
                continue
        else:
            # Für andere Einträge: Verwende timestamp
            entry_time_str = entry.get('timestamp')
            if not entry_time_str:
                continue
            
            try:
                if isinstance(entry_time_str, str):
                    entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
                else:
                    entry_time = entry_time_str
                
                if entry_time.tzinfo is None:
                    entry_time = tz_berlin.localize(entry_time.replace(tzinfo=None))
                elif entry_time.tzinfo != tz_berlin:
                    entry_time = entry_time.astimezone(tz_berlin)
                
                # Alle Einträge des Tages
                if entry_time.date() == selected_date:
                    # Berechne Stunden und Minuten
                    hour = entry_time.hour
                    minute = entry_time.minute
                    
                    timeline_events.append({
                        'category': entry.get('category', ''),
                        'time': entry_time,
                        'display': entry.get('display', ''),
                        'time_str': entry_time.strftime('%H:%M'),
                        'hour': hour,
                        'minute': minute
                    })
            except (ValueError, AttributeError):
                continue
    
    # Sortiere nach Zeit (nach Stunden und Minuten)
    def get_sort_key(event):
        if 'start_hour' in event:
            return event.get('start_hour', 0) * 60 + event.get('start_minute', 0)
        elif 'hour' in event:
            return event.get('hour', 0) * 60 + event.get('minute', 0)
        return 0
    
    timeline_events.sort(key=get_sort_key)
    wake_up_time_str = None
    
    # Nickerchen-Vorschläge berechnen (nur für heute)
    nap_suggestions = []
    baby_age_months = None
    if is_today:
        nap_suggestions = BabyInfo.get_nap_suggestions(selected_date)
        baby_age_months = BabyInfo.get_age_months()
    
    # Datum formatieren für Anzeige
    date_display = selected_date.strftime('%d.%m.%Y')
    if is_today:
        date_display = "Heute"
    elif selected_date == date.today() - timedelta(days=1):
        date_display = "Gestern"
    elif selected_date == date.today() - timedelta(days=2):
        date_display = "Vorgestern"
    
    return render_template('index.html',
                         sleep_status=sleep_status,
                         sleep_duration=sleep_duration,
                         awake_since=awake_since,
                         feeding_ago=feeding_ago,
                         diaper_ago=diaper_ago,
                         today_entries=entries,
                         active_sleep=active_sleep,
                         selected_date=selected_date.isoformat(),
                         prev_date=prev_date,
                         next_date=next_date,
                         date_display=date_display,
                         is_today=is_today,
                         sleep_since=sleep_since,
                         wake_up_time=wake_up_time_str,
                         timeline_events=timeline_events,
                         nap_suggestions=nap_suggestions,
                         baby_age_months=baby_age_months)

@bp.route('/settings/birth_date', methods=['POST'])
def set_birth_date():
    """Setzt das Geburtsdatum des Babys"""
    birth_date_str = request.form.get('birth_date')
    if not birth_date_str:
        flash('Bitte ein Geburtsdatum angeben', 'error')
        return redirect(url_for('main.index'))
    
    try:
        birth_date = date.fromisoformat(birth_date_str)
        BabyInfo.set_birth_date(birth_date)
        flash('Geburtsdatum gespeichert', 'success')
    except ValueError:
        flash('Ungültiges Datumsformat', 'error')
    
    return redirect(url_for('main.index'))

