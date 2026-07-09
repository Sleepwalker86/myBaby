from datetime import date
from urllib.parse import urlparse

from flask import Blueprint, request, redirect, url_for, session, flash

from app.models.models import BabyInfo
from app.i18n import _

bp = Blueprint('baby', __name__, url_prefix='/baby')


def _safe_redirect_target():
    """Wie request.referrer, aber nur wenn er auf dieselbe Origin zeigt (siehe Issue #40:
    Open Redirect über den Referer-Header bei anderen Routen - hier von Anfang an vermieden)."""
    referrer = request.referrer
    if referrer:
        parsed = urlparse(referrer)
        if not parsed.netloc or parsed.netloc == request.host:
            return referrer
    return url_for('main.index')


@bp.route('/switch/<int:baby_id>', methods=['POST'])
def switch(baby_id):
    """Wechselt das aktive Kind-Profil (Issue #33). Die Auswahl gilt pro Browser-Session,
    analog zur Sprachauswahl in app/i18n.py."""
    babies = BabyInfo.get_all_babies()
    if not any(b['id'] == baby_id for b in babies):
        flash(_('messages.error.invalid_input'), 'danger')
        return redirect(_safe_redirect_target())

    session['active_baby_id'] = baby_id
    return redirect(_safe_redirect_target())


@bp.route('/create', methods=['POST'])
def create():
    """Legt ein neues Kind-Profil an und wechselt direkt dorthin (Issue #33)."""
    name = request.form.get('name', '').strip()
    birth_date_str = request.form.get('birth_date', '').strip()

    if not name or not birth_date_str:
        flash(_('messages.error.all_fields_required'), 'danger')
        return redirect(_safe_redirect_target())

    try:
        birth_date = date.fromisoformat(birth_date_str)
    except ValueError:
        flash(_('messages.error.invalid_date'), 'danger')
        return redirect(_safe_redirect_target())

    new_baby_id = BabyInfo.create_baby(name, birth_date)
    session['active_baby_id'] = new_baby_id
    flash(_('messages.success.baby_created'), 'success')
    return redirect(_safe_redirect_target())


@bp.route('/<int:baby_id>/update', methods=['POST'])
def update(baby_id):
    """Bearbeitet Name/Geburtsdatum/Geschlecht eines (nicht notwendigerweise aktiven) Kind-Profils."""
    name = request.form.get('name', '').strip()
    birth_date_str = request.form.get('birth_date', '').strip()
    gender = request.form.get('gender', '').strip()

    if not name or not birth_date_str:
        flash(_('messages.error.all_fields_required'), 'danger')
        return redirect(_safe_redirect_target())

    try:
        birth_date = date.fromisoformat(birth_date_str)
    except ValueError:
        flash(_('messages.error.invalid_date'), 'danger')
        return redirect(_safe_redirect_target())

    if gender not in ('m', 'f'):
        gender = ''

    BabyInfo.set_baby_info(name=name, birth_date=birth_date, gender=gender, baby_id=baby_id)
    flash(_('messages.success.baby_updated'), 'success')
    return redirect(_safe_redirect_target())


@bp.route('/<int:baby_id>/delete', methods=['POST'])
def delete(baby_id):
    """Löscht ein Kind-Profil. Wird verweigert, wenn es Tracking-Daten hat oder das letzte
    verbleibende Profil ist (siehe BabyInfo.delete_baby)."""
    try:
        BabyInfo.delete_baby(baby_id)
    except ValueError as e:
        if str(e) == 'last_baby':
            flash(_('messages.error.baby_last_one'), 'danger')
        else:
            flash(_('messages.error.baby_has_data'), 'danger')
        return redirect(_safe_redirect_target())

    if session.get('active_baby_id') == baby_id:
        session.pop('active_baby_id', None)

    flash(_('messages.success.baby_deleted'), 'success')
    return redirect(_safe_redirect_target())
