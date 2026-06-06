from flask import Blueprint, request, redirect, url_for, flash

from app.form_datetime import normalize_form_datetime
from app.models.models import Illness

bp = Blueprint('illness', __name__, url_prefix='/illness')


@bp.route('/create', methods=['POST'])
def create():
    start_time = normalize_form_datetime(request.form.get('start_time'))
    end_time = normalize_form_datetime(request.form.get('end_time'))
    illness_type = request.form.get('type') or 'Erkrankung'
    symptoms = request.form.get('symptoms') or None
    notes = request.form.get('notes') or None

    if not start_time:
        flash('Ungültiger Startzeitpunkt für Erkrankung.', 'danger')
        return redirect(url_for('main.index'))

    Illness.create(start_time, end_time, illness_type, symptoms, notes)
    flash('Erkrankung gespeichert.', 'success')
    return redirect(url_for('main.index'))


@bp.route('/<int:illness_id>/update', methods=['POST'])
def update(illness_id):
    start_time = normalize_form_datetime(request.form.get('start_time'))
    end_time = normalize_form_datetime(request.form.get('end_time'))
    illness_type = request.form.get('type') or 'Erkrankung'
    symptoms = request.form.get('symptoms') or None
    notes = request.form.get('notes') or None

    if not start_time:
        flash('Ungültiger Startzeitpunkt für Erkrankung.', 'danger')
        return redirect(request.referrer or url_for('entries.entries'))

    Illness.update(illness_id, start_time, end_time, illness_type, symptoms, notes)
    flash('Erkrankung aktualisiert.', 'success')
    return redirect(request.referrer or url_for('entries.entries'))


@bp.route('/<int:illness_id>/delete', methods=['POST'])
def delete(illness_id):
    Illness.delete(illness_id)
    flash('Erkrankung gelöscht.', 'success')
    return redirect(request.referrer or url_for('entries.entries'))
