from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Sleep, NightWaking

from app.form_datetime import normalize_form_datetime

from app.timezone import tz_berlin


def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    from datetime import datetime
    return datetime.now(tz_berlin).replace(microsecond=0)


def _effective_timestamp(form_key):
    """Liest und normalisiert einen Zeitstempel aus dem Formular; Fallback: jetzt (Berlin)."""
    raw = request.form.get(form_key)
    if raw and str(raw).strip():
        normalized = normalize_form_datetime(raw)
        if normalized:
            return normalized
    return get_local_now().isoformat()


bp = Blueprint('sleep', __name__, url_prefix='/sleep')


@bp.route('/nap/start', methods=['POST'])
def start_nap():
    """Startet ein Nickerchen"""
    if Sleep.get_active_sleep_by_type('nap'):
        flash('Nickerchen läuft bereits', 'warning')
        return redirect(url_for('main.index'))

    timestamp = _effective_timestamp('start_time')

    sleep_quality = request.form.get('sleep_quality') or None
    sleep_location = request.form.get('sleep_location') or None
    sleep_comment = request.form.get('sleep_comment') or None

    Sleep.create_nap(timestamp, sleep_quality=sleep_quality, sleep_location=sleep_location, sleep_comment=sleep_comment)
    flash('Nickerchen gestartet', 'success')
    return redirect(url_for('main.index'))


@bp.route('/nap/end', methods=['POST'])
def end_nap():
    """Beendet ein Nickerchen"""
    active_sleep = Sleep.get_active_sleep_by_type('nap')
    if active_sleep:
        timestamp = _effective_timestamp('end_time')
        Sleep.end_sleep(active_sleep['id'], timestamp)
        flash('Nickerchen beendet', 'success')
    else:
        flash('Kein aktives Nickerchen gefunden', 'warning')
    return redirect(url_for('main.index'))


@bp.route('/night/start', methods=['POST'])
def start_night_sleep():
    """Startet den Nachtschlaf"""
    if Sleep.get_active_sleep_by_type('night'):
        flash('Nachtschlaf läuft bereits', 'warning')
        return redirect(url_for('main.index'))

    timestamp = _effective_timestamp('start_time')

    sleep_quality = request.form.get('sleep_quality') or None
    sleep_location = request.form.get('sleep_location') or None
    sleep_comment = request.form.get('sleep_comment') or None

    Sleep.create_night_sleep(timestamp, sleep_quality=sleep_quality, sleep_location=sleep_location, sleep_comment=sleep_comment)
    flash('Nachtschlaf gestartet', 'success')
    return redirect(url_for('main.index'))


@bp.route('/night/end', methods=['POST'])
def end_night_sleep():
    """Beendet den Nachtschlaf"""
    active_sleep = Sleep.get_active_sleep_by_type('night')
    if active_sleep:
        timestamp = _effective_timestamp('end_time')
        Sleep.end_sleep(active_sleep['id'], timestamp)
        flash('Nachtschlaf beendet', 'success')
    else:
        flash('Kein aktiver Nachtschlaf gefunden', 'warning')
    return redirect(url_for('main.index'))


@bp.route('/night_waking/start', methods=['POST'])
def start_night_waking():
    """Startet ein nächtliches Aufwachen"""
    timestamp = _effective_timestamp('start_time')
    NightWaking.create(timestamp)
    flash('Nächtliches Aufwachen gestartet', 'success')
    return redirect(url_for('main.index'))


@bp.route('/night_waking/end', methods=['POST'])
def end_night_waking():
    """Beendet ein nächtliches Aufwachen"""
    active_waking = NightWaking.get_active()
    if active_waking:
        timestamp = _effective_timestamp('end_time')
        NightWaking.end_waking(active_waking['id'], timestamp)
        flash('Nächtliches Aufwachen beendet', 'success')
    else:
        flash('Kein aktives nächtliches Aufwachen gefunden', 'warning')
    return redirect(url_for('main.index'))
