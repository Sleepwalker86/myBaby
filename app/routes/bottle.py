from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Bottle
from app.form_datetime import normalize_form_datetime
from app.form_validation import parse_bounded_number
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    return datetime.now(tz_berlin).replace(microsecond=0)

bp = Blueprint('bottle', __name__, url_prefix='/bottle')

@bp.route('/create', methods=['POST'])
def create():
    """Erstellt einen Flaschen-Eintrag"""
    try:
        amount = parse_bounded_number(request.form.get('amount', 0), max_value=5000, cast=int)
    except ValueError:
        flash('Ungültige Menge', 'error')
        return redirect(url_for('main.index'))

    timestamp = normalize_form_datetime(request.form.get('timestamp', '')) or get_local_now().isoformat()
    Bottle.create(timestamp, amount)
    flash(f'Flasche ({amount} ml) erfasst', 'success')
    return redirect(url_for('main.index'))

