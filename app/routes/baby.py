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
