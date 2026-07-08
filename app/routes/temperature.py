from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Temperature
from app.form_validation import parse_bounded_number
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    return datetime.now(tz_berlin).replace(microsecond=0)

bp = Blueprint('temperature', __name__, url_prefix='/temperature')

@bp.route('/create', methods=['POST'])
def create():
    """Erstellt einen Temperatur-Eintrag"""
    try:
        value = parse_bounded_number(request.form.get('value', 0), max_value=42)
    except ValueError:
        flash('Ungültige Temperatur', 'error')
        return redirect(url_for('main.index'))
    
    timestamp = get_local_now().isoformat()
    Temperature.create(timestamp, value)
    flash(f'Temperatur ({value}°C) erfasst', 'success')
    return redirect(url_for('main.index'))

