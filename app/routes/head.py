from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import HeadCircumference
from app.i18n import _
from app.form_datetime import normalize_form_datetime
from app.form_validation import parse_bounded_number
from datetime import datetime

from app.timezone import tz_berlin

def get_local_now():
    return datetime.now(tz_berlin).replace(microsecond=0)

bp = Blueprint('head', __name__, url_prefix='/head')


@bp.route('/create', methods=['POST'])
def create():
    try:
        head_circumference_cm = parse_bounded_number(request.form.get('head_circumference_cm', 0), max_value=60)
    except ValueError:
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    if timestamp_raw and len(timestamp_raw) == 10:  # nur Datum (YYYY-MM-DD)
        naive = timestamp_raw + get_local_now().strftime('T%H:%M:%S')
        timestamp = normalize_form_datetime(naive) or get_local_now().isoformat()
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
        head_circumference_cm = parse_bounded_number(request.form.get('head_circumference_cm', 0), max_value=60)
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
    HeadCircumference.update(head_circumference_id, timestamp, head_circumference_cm, notes)
    flash(_('messages.success.head_updated'), 'success')
    return redirect(url_for('main.index'))
