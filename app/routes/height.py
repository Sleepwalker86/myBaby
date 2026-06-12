from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Height
from app.i18n import _
from app.form_datetime import normalize_form_datetime
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    return datetime.now(tz_berlin)

bp = Blueprint('height', __name__, url_prefix='/height')


@bp.route('/create', methods=['POST'])
def create():
    try:
        height_cm = float(request.form.get('height_cm', 0))
        if height_cm <= 0 or height_cm >= 200:
            raise ValueError()
    except (ValueError, TypeError):
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    if timestamp_raw and len(timestamp_raw) == 10:
        now = get_local_now()
        timestamp = timestamp_raw + now.strftime('T%H:%M:%S')
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
        height_cm = float(request.form.get('height_cm', 0))
        if height_cm <= 0 or height_cm >= 200:
            raise ValueError()
    except (ValueError, TypeError):
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    if timestamp_raw and len(timestamp_raw) == 10:
        now = get_local_now()
        timestamp = timestamp_raw + now.strftime('T%H:%M:%S')
    else:
        timestamp = normalize_form_datetime(timestamp_raw) or get_local_now().isoformat()
    Height.update(height_id, timestamp, height_cm, notes)
    flash(_('messages.success.height_updated'), 'success')
    return redirect(url_for('main.index'))
