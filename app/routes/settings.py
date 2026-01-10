from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.models import BabyInfo
from datetime import date

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/')
def settings():
    """Einstellungsseite"""
    baby_name = BabyInfo.get_name()
    baby_birth_date = BabyInfo.get_birth_date()
    baby_age_months = BabyInfo.get_age_months() if baby_birth_date else None
    
    return render_template('settings.html',
                         baby_name=baby_name,
                         baby_birth_date=baby_birth_date,
                         baby_age_months=baby_age_months)

@bp.route('/update', methods=['POST'])
def update_settings():
    """Aktualisiert die Einstellungen"""
    name = request.form.get('name', '').strip()
    birth_date_str = request.form.get('birth_date', '').strip()
    
    # Validiere und setze Geburtsdatum
    birth_date = None
    if birth_date_str:
        try:
            birth_date = date.fromisoformat(birth_date_str)
        except ValueError:
            flash('Ungültiges Datumsformat', 'error')
            return redirect(url_for('settings.settings'))
    
    # Setze Name und/oder Geburtsdatum
    BabyInfo.set_baby_info(name=name if name else None, birth_date=birth_date)
    
    flash('Einstellungen gespeichert', 'success')
    return redirect(url_for('settings.settings'))

