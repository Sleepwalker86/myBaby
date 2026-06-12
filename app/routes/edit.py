from flask import Blueprint, request, redirect, url_for, flash
from app.models.models import Sleep, Feeding, Bottle, Diaper, Temperature, Medicine, NightWaking, Porridge
from app.form_datetime import normalize_form_datetime

bp = Blueprint('edit', __name__, url_prefix='/edit')


@bp.route('/sleep/<int:sleep_id>', methods=['POST'])
def edit_sleep(sleep_id):
    """Bearbeitet einen Schlaf-Eintrag"""
    try:
        start_raw = request.form.get('start_time')
        start_time = normalize_form_datetime(start_raw) if start_raw and str(start_raw).strip() else None
        end_raw = request.form.get('end_time')
        end_time = normalize_form_datetime(end_raw) if end_raw and str(end_raw).strip() else None
        sleep_type = request.form.get('type')
        sleep_quality = request.form.get('sleep_quality') or None
        sleep_location = request.form.get('sleep_location') or None
        sc = request.form.get('sleep_comment')
        sleep_comment = sc.strip() if sc and str(sc).strip() else None

        if not start_time:
            flash('Startzeit ist erforderlich', 'error')
            return redirect(url_for('main.index'))

        Sleep.update(sleep_id, start_time, end_time, sleep_type, sleep_quality, sleep_location, sleep_comment)
        flash('Schlaf-Eintrag aktualisiert', 'success')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/sleep/<int:sleep_id>/delete', methods=['POST'])
def delete_sleep(sleep_id):
    """Löscht einen Schlaf-Eintrag"""
    try:
        Sleep.delete(sleep_id)
        flash('Schlaf-Eintrag gelöscht', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/feeding/<int:feeding_id>', methods=['POST'])
def edit_feeding(feeding_id):
    """Bearbeitet einen Still-Eintrag"""
    try:
        ts_raw = request.form.get('timestamp')
        timestamp = normalize_form_datetime(ts_raw) if ts_raw and str(ts_raw).strip() else None
        side = request.form.get('side')
        end_raw = request.form.get('end_time')
        end_time = normalize_form_datetime(end_raw) if end_raw and str(end_raw).strip() else None

        if not timestamp or side not in ['links', 'rechts']:
            flash('Ungültige Eingabe', 'error')
            return redirect(url_for('main.index'))

        Feeding.update(feeding_id, timestamp, side, end_time)
        flash('Still-Eintrag aktualisiert', 'success')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/feeding/<int:feeding_id>/delete', methods=['POST'])
def delete_feeding(feeding_id):
    """Löscht einen Still-Eintrag"""
    try:
        Feeding.delete(feeding_id)
        flash('Still-Eintrag gelöscht', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/bottle/<int:bottle_id>', methods=['POST'])
def edit_bottle(bottle_id):
    """Bearbeitet einen Flaschen-Eintrag"""
    try:
        ts_raw = request.form.get('timestamp')
        timestamp = normalize_form_datetime(ts_raw) if ts_raw and str(ts_raw).strip() else None
        amount = int(request.form.get('amount', 0))

        if not timestamp or amount <= 0:
            flash('Ungültige Eingabe', 'error')
            return redirect(url_for('main.index'))

        Bottle.update(bottle_id, timestamp, amount)
        flash('Flasche-Eintrag aktualisiert', 'success')
    except (ValueError, TypeError):
        flash('Ungültige Menge', 'error')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/bottle/<int:bottle_id>/delete', methods=['POST'])
def delete_bottle(bottle_id):
    """Löscht einen Flaschen-Eintrag"""
    try:
        Bottle.delete(bottle_id)
        flash('Flasche-Eintrag gelöscht', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/diaper/<int:diaper_id>', methods=['POST'])
def edit_diaper(diaper_id):
    """Bearbeitet einen Windel-Eintrag"""
    try:
        ts_raw = request.form.get('timestamp')
        timestamp = normalize_form_datetime(ts_raw) if ts_raw and str(ts_raw).strip() else None
        diaper_type = request.form.get('type')

        if not timestamp or diaper_type not in ['nass', 'groß', 'beides']:
            flash('Ungültige Eingabe', 'error')
            return redirect(url_for('main.index'))

        Diaper.update(diaper_id, timestamp, diaper_type)
        flash('Windel-Eintrag aktualisiert', 'success')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/diaper/<int:diaper_id>/delete', methods=['POST'])
def delete_diaper(diaper_id):
    """Löscht einen Windel-Eintrag"""
    try:
        Diaper.delete(diaper_id)
        flash('Windel-Eintrag gelöscht', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/temperature/<int:temp_id>', methods=['POST'])
def edit_temperature(temp_id):
    """Bearbeitet einen Temperatur-Eintrag"""
    try:
        ts_raw = request.form.get('timestamp')
        timestamp = normalize_form_datetime(ts_raw) if ts_raw and str(ts_raw).strip() else None
        value = float(request.form.get('value', 0))

        if not timestamp or value <= 0 or value > 42:
            flash('Ungültige Eingabe', 'error')
            return redirect(url_for('main.index'))

        Temperature.update(temp_id, timestamp, value)
        flash('Temperatur-Eintrag aktualisiert', 'success')
    except (ValueError, TypeError):
        flash('Ungültige Temperatur', 'error')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/temperature/<int:temp_id>/delete', methods=['POST'])
def delete_temperature(temp_id):
    """Löscht einen Temperatur-Eintrag"""
    try:
        Temperature.delete(temp_id)
        flash('Temperatur-Eintrag gelöscht', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/medicine/<int:med_id>', methods=['POST'])
def edit_medicine(med_id):
    """Bearbeitet einen Medizin-Eintrag"""
    try:
        ts_raw = request.form.get('timestamp')
        timestamp = normalize_form_datetime(ts_raw) if ts_raw and str(ts_raw).strip() else None
        name = request.form.get('name', '').strip()
        dose = request.form.get('dose', '').strip()

        if not timestamp or not name or not dose:
            flash('Alle Felder sind erforderlich', 'error')
            return redirect(url_for('main.index'))

        Medicine.update(med_id, timestamp, name, dose)
        flash('Medizin-Eintrag aktualisiert', 'success')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/medicine/<int:med_id>/delete', methods=['POST'])
def delete_medicine(med_id):
    """Löscht einen Medizin-Eintrag"""
    try:
        Medicine.delete(med_id)
        flash('Medizin-Eintrag gelöscht', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/night_waking/<int:waking_id>', methods=['POST'])
def edit_night_waking(waking_id):
    """Bearbeitet einen nächtliches Aufwachen-Eintrag"""
    try:
        start_raw = request.form.get('start_time')
        start_time = normalize_form_datetime(start_raw) if start_raw and str(start_raw).strip() else None
        end_raw = request.form.get('end_time')
        end_time = normalize_form_datetime(end_raw) if end_raw and str(end_raw).strip() else None

        if not start_time:
            flash('Startzeit ist erforderlich', 'error')
            return redirect(url_for('main.index'))

        NightWaking.update(waking_id, start_time, end_time)
        flash('Nächtliches Aufwachen aktualisiert', 'success')
    except Exception as e:
        flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/night_waking/<int:waking_id>/delete', methods=['POST'])
def delete_night_waking(waking_id):
    """Löscht einen nächtliches Aufwachen-Eintrag"""
    try:
        NightWaking.delete(waking_id)
        flash('Nächtliches Aufwachen gelöscht', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen: {str(e)}', 'error')
    return redirect(url_for('main.index'))


@bp.route('/porridge/<int:porridge_id>', methods=['POST'])
def edit_porridge(porridge_id):
    """Bearbeitet einen Brei-Eintrag"""
    try:
        amount = int(request.form.get('amount', 0))
        if amount <= 0 or amount > 2000:
            raise ValueError()
    except (ValueError, TypeError):
        flash('Ungültige Menge', 'error')
        return redirect(url_for('main.index'))

    food = request.form.get('food', '').strip() or None
    timestamp_raw = request.form.get('timestamp', '')
    timestamp = normalize_form_datetime(timestamp_raw) if timestamp_raw.strip() else None
    if not timestamp:
        flash('Zeitstempel ist erforderlich', 'error')
        return redirect(url_for('main.index'))
    Porridge.update(porridge_id, timestamp, amount, food)
    flash('Brei-Eintrag aktualisiert', 'success')
    return redirect(url_for('main.index'))


@bp.route('/porridge/<int:porridge_id>/delete', methods=['POST'])
def delete_porridge(porridge_id):
    """Löscht einen Brei-Eintrag"""
    try:
        Porridge.delete(porridge_id)
        flash('Brei-Eintrag gelöscht', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen: {str(e)}', 'error')
    return redirect(url_for('main.index'))
