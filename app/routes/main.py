from flask import Blueprint, render_template, request
from app.models.models import (
    Sleep, Feeding, Bottle, Diaper, get_all_entries_today
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
    sleep_duration = Sleep.get_today_sleep_duration(selected_date)
    
    # Zeit seit letztem Aufwachen (nur für heute)
    awake_since = None
    if is_today:
        if active_sleep:
            awake_since = None  # Baby schläft
        else:
            # Suche den letzten beendeten Schlaf
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
                         is_today=is_today)

