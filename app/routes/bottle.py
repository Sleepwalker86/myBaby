from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Bottle
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    return datetime.now(tz_berlin)

bp = Blueprint('bottle', __name__, url_prefix='/bottle')

@bp.route('/create', methods=['POST'])
def create():
    """Erstellt einen Flaschen-Eintrag"""
    try:
        amount = int(request.form.get('amount', 0))
        if amount <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        flash('Ungültige Menge', 'error')
        return redirect(url_for('main.index'))
    
    timestamp = get_local_now().isoformat()
    Bottle.create(timestamp, amount)
    flash(f'Flasche ({amount} ml) erfasst', 'success')
    return redirect(url_for('main.index'))

