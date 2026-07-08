from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Weight
from app.i18n import _
from app.form_datetime import normalize_form_datetime
from app.form_validation import parse_bounded_number
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    return datetime.now(tz_berlin)

bp = Blueprint('weight', __name__, url_prefix='/weight')


@bp.route('/create', methods=['POST'])
def create():
    try:
        weight_kg = parse_bounded_number(request.form.get('weight_kg', 0), max_value=50)
    except ValueError:
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    if timestamp_raw and len(timestamp_raw) == 10:  # nur Datum (YYYY-MM-DD)
        now = get_local_now()
        timestamp = timestamp_raw + now.strftime('T%H:%M:%S')
    else:
        timestamp = normalize_form_datetime(timestamp_raw) or get_local_now().isoformat()
    Weight.create(timestamp, weight_kg, notes)
    flash(_('messages.success.weight_recorded').format(weight=weight_kg), 'success')
    return redirect(url_for('main.index'))


@bp.route('/delete/<int:weight_id>', methods=['POST'])
def delete(weight_id):
    Weight.delete(weight_id)
    flash(_('messages.success.weight_deleted'), 'success')
    return redirect(url_for('main.index'))


@bp.route('/update/<int:weight_id>', methods=['POST'])
def update(weight_id):
    try:
        weight_kg = parse_bounded_number(request.form.get('weight_kg', 0), max_value=50)
    except ValueError:
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    if timestamp_raw and len(timestamp_raw) == 10:  # nur Datum (YYYY-MM-DD)
        now = get_local_now()
        timestamp = timestamp_raw + now.strftime('T%H:%M:%S')
    else:
        timestamp = normalize_form_datetime(timestamp_raw) or get_local_now().isoformat()
    Weight.update(weight_id, timestamp, weight_kg, notes)
    flash(_('messages.success.weight_updated'), 'success')
    return redirect(url_for('main.index'))
