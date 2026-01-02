from flask import Blueprint, request, redirect, url_for, flash, jsonify
from app.models.models import Sleep, Feeding, Bottle, Diaper, Temperature, Medicine
from datetime import datetime

bp = Blueprint('edit', __name__, url_prefix='/edit')

@bp.route('/sleep/<int:sleep_id>', methods=['POST'])
def edit_sleep(sleep_id):
    """Bearbeitet einen Schlaf-Eintrag"""
    try:
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time') or None
        sleep_type = request.form.get('type')
        
        if not start_time:
            flash('Startzeit ist erforderlich', 'error')
            return redirect(url_for('main.index'))
        
        Sleep.update(sleep_id, start_time, end_time, sleep_type)
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
        timestamp = request.form.get('timestamp')
        side = request.form.get('side')
        
        if not timestamp or side not in ['links', 'rechts']:
            flash('Ungültige Eingabe', 'error')
            return redirect(url_for('main.index'))
        
        Feeding.update(feeding_id, timestamp, side)
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
        timestamp = request.form.get('timestamp')
        amount = int(request.form.get('amount', 0))
        
        if not timestamp or amount <= 0:
            flash('Ungültige Eingabe', 'error')
            return redirect(url_for('main.index'))
        
        Bottle.update(bottle_id, timestamp, amount)
        flash('Flasche-Eintrag aktualisiert', 'success')
    except (ValueError, TypeError) as e:
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
        timestamp = request.form.get('timestamp')
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
        timestamp = request.form.get('timestamp')
        value = float(request.form.get('value', 0))
        
        if not timestamp or value <= 0 or value > 45:
            flash('Ungültige Eingabe', 'error')
            return redirect(url_for('main.index'))
        
        Temperature.update(temp_id, timestamp, value)
        flash('Temperatur-Eintrag aktualisiert', 'success')
    except (ValueError, TypeError) as e:
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
        timestamp = request.form.get('timestamp')
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

