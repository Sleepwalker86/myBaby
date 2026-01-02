from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Sleep
from datetime import datetime
import pytz

# Zeitzone für Deutschland/Berlin
tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    return datetime.now(tz_berlin)

bp = Blueprint('sleep', __name__, url_prefix='/sleep')

@bp.route('/nap/start', methods=['POST'])
def start_nap():
    """Startet ein Nickerchen"""
    timestamp = get_local_now().isoformat()
    sleep_id = Sleep.create_nap(timestamp)
    flash('Nickerchen gestartet', 'success')
    return redirect(url_for('main.index'))

@bp.route('/nap/end', methods=['POST'])
def end_nap():
    """Beendet ein Nickerchen"""
    active_sleep = Sleep.get_active_sleep()
    if active_sleep and active_sleep['type'] == 'nap':
        timestamp = get_local_now().isoformat()
        Sleep.end_sleep(active_sleep['id'], timestamp)
        flash('Nickerchen beendet', 'success')
    else:
        flash('Kein aktives Nickerchen gefunden', 'warning')
    return redirect(url_for('main.index'))

@bp.route('/night/start', methods=['POST'])
def start_night_sleep():
    """Startet den Nachtschlaf"""
    timestamp = get_local_now().isoformat()
    sleep_id = Sleep.create_night_sleep(timestamp)
    flash('Nachtschlaf gestartet', 'success')
    return redirect(url_for('main.index'))

@bp.route('/night/end', methods=['POST'])
def end_night_sleep():
    """Beendet den Nachtschlaf"""
    active_sleep = Sleep.get_active_sleep()
    if active_sleep and active_sleep['type'] == 'night':
        timestamp = get_local_now().isoformat()
        Sleep.end_sleep(active_sleep['id'], timestamp)
        flash('Nachtschlaf beendet', 'success')
    else:
        flash('Kein aktiver Nachtschlaf gefunden', 'warning')
    return redirect(url_for('main.index'))

