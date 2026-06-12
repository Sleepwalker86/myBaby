from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Weight
from app.i18n import _
from app.form_datetime import normalize_form_datetime
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    return datetime.now(tz_berlin)

bp = Blueprint('weight', __name__, url_prefix='/weight')


@bp.route('/create', methods=['POST'])
def create():
    try:
        weight_kg = float(request.form.get('weight_kg', 0))
        if weight_kg <= 0 or weight_kg >= 50:
            raise ValueError()
    except (ValueError, TypeError):
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
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
        weight_kg = float(request.form.get('weight_kg', 0))
        if weight_kg <= 0 or weight_kg >= 50:
            raise ValueError()
    except (ValueError, TypeError):
        flash(_('messages.error.invalid_input'), 'error')
        return redirect(url_for('main.index'))

    notes = request.form.get('notes', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    timestamp = normalize_form_datetime(timestamp_raw) or get_local_now().isoformat()
    Weight.update(weight_id, timestamp, weight_kg, notes)
    flash(_('messages.success.weight_updated'), 'success')
    return redirect(url_for('main.index'))
