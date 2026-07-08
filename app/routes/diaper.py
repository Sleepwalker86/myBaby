from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Diaper
from app.form_datetime import normalize_form_datetime
from datetime import datetime

from app.timezone import tz_berlin

def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    return datetime.now(tz_berlin).replace(microsecond=0)

bp = Blueprint('diaper', __name__, url_prefix='/diaper')

@bp.route('/create', methods=['POST'])
def create():
    """Erstellt einen Windel-Eintrag"""
    diaper_type = request.form.get('type')
    if diaper_type not in ['nass', 'groß', 'beides']:
        flash('Ungültiger Windeltyp', 'error')
        return redirect(url_for('main.index'))

    timestamp = normalize_form_datetime(request.form.get('timestamp', '')) or get_local_now().isoformat()
    Diaper.create(timestamp, diaper_type)
    flash(f'Windel ({diaper_type}) erfasst', 'success')
    return redirect(url_for('main.index'))

