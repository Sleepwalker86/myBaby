from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from app.models.models import (
    Sleep, Feeding, Bottle, Porridge, Diaper, get_all_entries_today, BabyInfo, NightWaking, Illness
)
from app.models.database import get_db, get_active_baby_id
from app.i18n import _
from datetime import datetime, date, timedelta
import os

def get_baby_name():
    """Hilfsfunktion zum Abrufen des Baby-Namens"""
    return BabyInfo.get_name()

from app.timezone import tz_berlin, to_berlin

bp = Blueprint('main', __name__)

def format_time_ago(timestamp):
    """Formatiert eine Zeitstempel als 'vor X Stunden/Minuten'"""
    if not timestamp:
        return _('status.never')

    try:
        now = datetime.now(tz_berlin)
        ts = to_berlin(timestamp)
        diff = now - ts
        total_seconds = int(diff.total_seconds())
        
        if total_seconds < 0:
            return _('common.just_now')
        
        # Wenn länger als 48 Stunden (172800 Sekunden) her, zeige "Noch nie"
        if total_seconds > 48 * 3600:
            return _('status.never')
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            if minutes > 0:
                return _('common.ago_hours_minutes', hours=hours, minutes=minutes)
            return _('common.ago_hours', hours=hours)
        elif minutes > 0:
            return _('common.ago_minutes', minutes=minutes)
        else:
            return _('common.just_now')
    except (ValueError, AttributeError):
        return _('common.unknown')

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
    berlin_today = datetime.now(tz_berlin).date()
    # Datum aus Request (Standard: heute in Europe/Berlin)
    selected_date_str = request.args.get('date', berlin_today.isoformat())
    try:
        selected_date = date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = berlin_today
    
    # Vorheriger und nächster Tag
    prev_date = (selected_date - timedelta(days=1)).isoformat()
    next_date = (selected_date + timedelta(days=1)).isoformat()
    is_today = selected_date == berlin_today
    
    # Aktueller Schlafstatus (nur für heute relevant)
    active_sleep = Sleep.get_active_sleep() if is_today else None
    sleep_status = _('status.sleeping') if active_sleep else _('status.awake')
    
    # Aktives nächtliches Aufwachen (nur für heute relevant)
    active_night_waking = NightWaking.get_active() if is_today else None
    
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
                'SELECT end_time FROM sleep WHERE end_time IS NOT NULL AND baby_id = ? ORDER BY end_time DESC LIMIT 1',
                (get_active_baby_id(),)
            ).fetchone()
            if last_sleep:
                awake_since = format_time_ago(last_sleep['end_time'])
            else:
                awake_since = _('common.today')
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
        # Überspringe nächtliches Aufwachen - soll nicht im Kreisdiagramm angezeigt werden
        if entry.get('category') == 'night_waking':
            continue
        
        # Für Schlaf-Einträge: Unterscheide zwischen Nachtschlaf und Nickerchen
        if entry.get('category') == 'sleep':
            start_time_str = entry.get('timestamp') or entry.get('start_time')
            end_time_str = entry.get('end_time')
            sleep_type = entry.get('type', 'night')
            
            if not start_time_str or not end_time_str:
                continue
            
            try:
                # Parse Start- und Endzeit
                start_time = to_berlin(start_time_str)
                end_time = to_berlin(end_time_str)

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
                entry_time = to_berlin(entry_time_str)

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
    
    # Nickerchen- und Nachtschlaf-Vorschläge berechnen (nur für heute)
    nap_suggestions = []
    night_sleep_suggestion = None
    baby_age_months = None
    sleep_meta = BabyInfo.get_sleep_meta_settings()
    if is_today:
        nap_suggestions = BabyInfo.get_nap_suggestions(selected_date)
        night_sleep_suggestion = BabyInfo.get_night_sleep_suggestion(selected_date)
        baby_age_months = BabyInfo.get_age_months()
    
    # Datum formatieren für Anzeige
    date_display = selected_date.strftime('%d.%m.%Y')
    if is_today:
        date_display = _('common.today')
    elif selected_date == berlin_today - timedelta(days=1):
        date_display = _('common.yesterday')
    elif selected_date == berlin_today - timedelta(days=2):
        date_display = _('common.day_before_yesterday')
    
    # Baby-Name für persönlichere Anzeige
    baby_name = BabyInfo.get_name()
    show_audio_player = BabyInfo.get_show_audio_player()

    return render_template('index.html',
                         sleep_status=sleep_status,
                         sleep_duration=sleep_duration,
                         awake_since=awake_since,
                         feeding_ago=feeding_ago,
                         diaper_ago=diaper_ago,
                         today_entries=entries,
                         active_sleep=active_sleep,
                         active_night_waking=active_night_waking,
                         selected_date=selected_date.isoformat(),
                         prev_date=prev_date,
                         next_date=next_date,
                         date_display=date_display,
                         is_today=is_today,
                         sleep_since=sleep_since,
                         wake_up_time=wake_up_time_str,
                         timeline_events=timeline_events,
                         nap_suggestions=nap_suggestions,
                         night_sleep_suggestion=night_sleep_suggestion,
                         baby_age_months=baby_age_months,
                         baby_name=baby_name,
                         sleep_meta=sleep_meta,
                         show_audio_player=show_audio_player,
                         now_date=datetime.now(tz_berlin).date().isoformat())

@bp.route('/api/audio-files')
def get_audio_files():
    """Gibt eine Liste aller verfügbaren Audio-Dateien zurück"""
    static_folder = current_app.static_folder
    audio_dir = os.path.join(static_folder, 'audio')
    audio_files = []
    if os.path.exists(audio_dir):
        for file in os.listdir(audio_dir):
            if file.endswith(('.mp3', '.wav', '.ogg', '.m4a')) and not file.startswith('.'):
                audio_files.append(file)
    return jsonify(sorted(audio_files))

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

