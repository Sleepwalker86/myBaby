from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Medicine
from app.form_datetime import normalize_form_datetime
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    """Gibt die aktuelle Zeit in der Berliner Zeitzone zurück"""
    return datetime.now(tz_berlin)

bp = Blueprint('medicine', __name__, url_prefix='/medicine')

@bp.route('/create', methods=['POST'])
def create():
    """Erstellt einen Medizin-Eintrag"""
    name = request.form.get('name', '').strip()
    dose = request.form.get('dose', '').strip()

    if not name or not dose:
        flash('Medikamentenname und Dosis sind erforderlich', 'error')
        return redirect(url_for('main.index'))

    timestamp = normalize_form_datetime(request.form.get('timestamp', '')) or get_local_now().isoformat()
    Medicine.create(timestamp, name, dose)
    flash(f'Medizin ({name}, {dose}) erfasst', 'success')
    return redirect(url_for('main.index'))

