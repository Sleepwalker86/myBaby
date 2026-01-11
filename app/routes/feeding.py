from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Feeding
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    return datetime.now(tz_berlin)

bp = Blueprint('feeding', __name__, url_prefix='/feeding')

@bp.route('/create', methods=['POST'])
def create():
    """Erstellt einen Still-Eintrag"""
    side = request.form.get('side')
    if side not in ['links', 'rechts']:
        flash('Ungültige Brustseite', 'error')
        return redirect(url_for('main.index'))
    
    # Hole Startzeit aus Formular oder verwende aktuelle Zeit
    start_time_str = request.form.get('start_time')
    if start_time_str:
        try:
            # Konvertiere datetime-local Format zu ISO
            start_dt = datetime.fromisoformat(start_time_str.replace('Z', ''))
            if start_dt.tzinfo is None:
                start_dt = tz_berlin.localize(start_dt)
            timestamp = start_dt.isoformat()
        except (ValueError, AttributeError):
            timestamp = get_local_now().isoformat()
    else:
        timestamp = get_local_now().isoformat()
    
    # Hole optionale Endzeit
    end_time = None
    end_time_str = request.form.get('end_time')
    if end_time_str:
        try:
            end_dt = datetime.fromisoformat(end_time_str.replace('Z', ''))
            if end_dt.tzinfo is None:
                end_dt = tz_berlin.localize(end_dt)
            end_time = end_dt.isoformat()
        except (ValueError, AttributeError):
            pass
    
    Feeding.create(timestamp, side, end_time)
    flash(f'Stillen ({side}) erfasst', 'success')
    return redirect(url_for('main.index'))

