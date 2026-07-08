from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Feeding
import pytz

from app.form_datetime import normalize_form_datetime

tz_berlin = pytz.timezone('Europe/Berlin')


def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    from datetime import datetime
    return datetime.now(tz_berlin).replace(microsecond=0)


bp = Blueprint('feeding', __name__, url_prefix='/feeding')


@bp.route('/create', methods=['POST'])
def create():
    """Erstellt einen Still-Eintrag"""
    side = request.form.get('side')
    if side not in ['links', 'rechts']:
        flash('Ungültige Brustseite', 'error')
        return redirect(url_for('main.index'))

    start_time_str = request.form.get('start_time')
    if start_time_str and str(start_time_str).strip():
        timestamp = normalize_form_datetime(start_time_str) or get_local_now().isoformat()
    else:
        timestamp = get_local_now().isoformat()

    end_time = None
    end_time_str = request.form.get('end_time')
    if end_time_str and str(end_time_str).strip():
        end_time = normalize_form_datetime(end_time_str)

    Feeding.create(timestamp, side, end_time)
    flash(f'Stillen ({side}) erfasst', 'success')
    return redirect(url_for('main.index'))
