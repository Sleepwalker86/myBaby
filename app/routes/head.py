from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import HeadCircumference
from app.i18n import _
from app.form_datetime import normalize_form_datetime
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    return datetime.now(tz_berlin)

bp = Blueprint('head', __name__, url_prefix='/head')


@bp.route('/create', methods=['POST'])
def create():
    try:
        head_circumference_cm = float(request.form.get('head_circumference_cm', 0))
        if head_circumference_cm <= 0 or head_circumference_cm >= 60:
            raise ValueError()
    except (ValueError, TypeError):
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    if timestamp_raw and len(timestamp_raw) == 10:  # nur Datum (YYYY-MM-DD)
        now = get_local_now()
        timestamp = timestamp_raw + now.strftime('T%H:%M:%S')
    else:
        timestamp = normalize_form_datetime(timestamp_raw) or get_local_now().isoformat()
    HeadCircumference.create(timestamp, head_circumference_cm, notes)
    flash(_('messages.success.head_recorded').format(head_circumference=head_circumference_cm), 'success')
    return redirect(url_for('main.index'))


@bp.route('/delete/<int:head_circumference_id>', methods=['POST'])
def delete(head_circumference_id):
    HeadCircumference.delete(head_circumference_id)
    flash(_('messages.success.head_deleted'), 'success')
    return redirect(url_for('main.index'))


@bp.route('/update/<int:head_circumference_id>', methods=['POST'])
def update(head_circumference_id):
    try:
        head_circumference_cm = float(request.form.get('head_circumference_cm', 0))
        if head_circumference_cm <= 0 or head_circumference_cm >= 60:
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
    HeadCircumference.update(head_circumference_id, timestamp, head_circumference_cm, notes)
    flash(_('messages.success.head_updated'), 'success')
    return redirect(url_for('main.index'))
