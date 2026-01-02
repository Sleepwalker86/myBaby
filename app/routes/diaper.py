from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Diaper
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    return datetime.now(tz_berlin)

bp = Blueprint('diaper', __name__, url_prefix='/diaper')

@bp.route('/create', methods=['POST'])
def create():
    """Erstellt einen Windel-Eintrag"""
    diaper_type = request.form.get('type')
    if diaper_type not in ['nass', 'groß', 'beides']:
        flash('Ungültiger Windeltyp', 'error')
        return redirect(url_for('main.index'))
    
    timestamp = get_local_now().isoformat()
    Diaper.create(timestamp, diaper_type)
    flash(f'Windel ({diaper_type}) erfasst', 'success')
    return redirect(url_for('main.index'))

