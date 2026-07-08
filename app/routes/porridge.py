from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Porridge
from app.i18n import _
from app.form_datetime import normalize_form_datetime
from app.form_validation import parse_bounded_number
from datetime import datetime
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

def get_local_now():
    return datetime.now(tz_berlin).replace(microsecond=0)

bp = Blueprint('porridge', __name__, url_prefix='/porridge')

@bp.route('/create', methods=['POST'])
def create():
    try:
        amount = parse_bounded_number(request.form.get('amount', 0), max_value=2000, cast=int)
    except ValueError:
        flash(_('messages.error.invalid_amount'), 'error')
        return redirect(url_for('main.index'))

    food = request.form.get('food', '').strip() or None
    timestamp = normalize_form_datetime(request.form.get('timestamp', '')) or get_local_now().isoformat()
    Porridge.create(timestamp, amount, food)
    msg = _('messages.success.porridge_recorded').format(amount=amount)
    if food:
        msg += f' – {food}'
    flash(msg, 'success')
    return redirect(url_for('main.index'))

@bp.route('/delete/<int:porridge_id>', methods=['POST'])
def delete(porridge_id):
    Porridge.delete(porridge_id)
    flash(_('messages.success.porridge_deleted'), 'success')
    return redirect(url_for('main.index'))

@bp.route('/update/<int:porridge_id>', methods=['POST'])
def update(porridge_id):
    try:
        amount = parse_bounded_number(request.form.get('amount', 0), max_value=2000, cast=int)
    except ValueError:
        flash(_('messages.error.invalid_amount'), 'error')
        return redirect(url_for('main.index'))

    food = request.form.get('food', '').strip() or None
    timestamp = normalize_form_datetime(request.form.get('timestamp', '')) or get_local_now().isoformat()
    Porridge.update(porridge_id, timestamp, amount, food)
    flash(_('messages.success.porridge_updated'), 'success')
    return redirect(url_for('main.index'))
