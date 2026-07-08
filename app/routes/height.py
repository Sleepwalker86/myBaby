from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Height
from app.i18n import _
from app.form_datetime import normalize_form_datetime
from app.form_validation import parse_bounded_number
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    return datetime.now(tz_berlin).replace(microsecond=0)

bp = Blueprint('height', __name__, url_prefix='/height')


@bp.route('/create', methods=['POST'])
def create():
    try:
        height_cm = parse_bounded_number(request.form.get('height_cm', 0), max_value=200)
    except ValueError:
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    if timestamp_raw and len(timestamp_raw) == 10:
        naive = timestamp_raw + get_local_now().strftime('T%H:%M:%S')
        timestamp = normalize_form_datetime(naive) or get_local_now().isoformat()
    else:
        timestamp = normalize_form_datetime(timestamp_raw) or get_local_now().isoformat()
    Height.create(timestamp, height_cm, notes)
    flash(_('messages.success.height_recorded').format(height=height_cm), 'success')
    return redirect(url_for('main.index'))


@bp.route('/delete/<int:height_id>', methods=['POST'])
def delete(height_id):
    Height.delete(height_id)
    flash(_('messages.success.height_deleted'), 'success')
    return redirect(url_for('main.index'))


@bp.route('/update/<int:height_id>', methods=['POST'])
def update(height_id):
    try:
        height_cm = parse_bounded_number(request.form.get('height_cm', 0), max_value=200)
    except ValueError:
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    if timestamp_raw and len(timestamp_raw) == 10:
        naive = timestamp_raw + get_local_now().strftime('T%H:%M:%S')
        timestamp = normalize_form_datetime(naive) or get_local_now().isoformat()
    else:
        timestamp = normalize_form_datetime(timestamp_raw) or get_local_now().isoformat()
    Height.update(height_id, timestamp, height_cm, notes)
    flash(_('messages.success.height_updated'), 'success')
    return redirect(url_for('main.index'))
