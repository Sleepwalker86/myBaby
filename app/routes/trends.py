from flask import Blueprint, render_template, request
from app.models.models import Sleep, Temperature, Diaper, Feeding, Illness, Weight, Height, BabyInfo
from app.models.growth_reference import get_weight_percentiles, get_height_percentiles
from datetime import datetime, date, timedelta

bp = Blueprint('trends', __name__, url_prefix='/trends')

def format_time(hours):
    """Formatiert Stunden in HH:MM Format"""
    if hours is None or hours == 0:
        return "00:00"
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h:02d}:{m:02d}"

def _age_months_at(birth_date, timestamp_str):
    """Berechnet das Alter in Monaten (als Fließkommazahl) an einem gegebenen Zeitpunkt."""
    try:
        entry_date = date.fromisoformat(str(timestamp_str)[:10])
    except ValueError:
        return None
    delta_days = (entry_date - birth_date).days
    return max(0.0, delta_days / 30.4375)

def _attach_percentiles(entries, gender, birth_date, percentile_fn):
    """Ergänzt jeden Eintrag um p3/p15/p50/p85/p97, passend zum Alter am jeweiligen
    Zeitpunkt. Rein additiv - ohne gesetztes Geschlecht bleiben die Einträge unverändert."""
    if not gender or not birth_date:
        return entries
    for entry in entries:
        age_months = _age_months_at(birth_date, entry.get('timestamp'))
        percentiles = percentile_fn(gender, age_months) if age_months is not None else None
        if percentiles:
            entry.update(percentiles)
    return entries

@bp.route('/')
def trends():
    """Trends und Statistiken Seite"""
    # Standard: Letzte 7 Tage
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=7)).isoformat()
    
    # Filter aus Request
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')
    
    # Statistiken holen
    stats = Sleep.get_sleep_statistics(start_date, end_date)
    
    # Uhrzeiten formatieren
    stats['avg_wake_time_formatted'] = format_time(stats['avg_wake_time'])
    stats['avg_sleep_time_formatted'] = format_time(stats['avg_sleep_time'])
    
    # Temperatur-Statistiken holen
    temp_stats = Temperature.get_temperature_statistics(start_date, end_date)
    
    # Windel-Statistiken holen
    diaper_stats = Diaper.get_diaper_statistics(start_date, end_date)
    
    # Still-Statistiken holen
    feeding_stats = Feeding.get_feeding_statistics(start_date, end_date)
    
    # Erkrankungs-Statistiken holen
    illness_stats = Illness.get_illness_statistics(start_date, end_date)

    # Gewichts- und Größen-Daten holen (alle, nicht nur im Zeitraum – für Wachstumskurve)
    weight_entries = Weight.get_all()
    height_entries = Height.get_all()

    # WHO-Perzentilen ergänzen, sofern Geschlecht und Geburtsdatum gesetzt sind.
    # Ohne Geschlecht bleibt das Chart exakt wie bisher (keine Bänder, kein Fehler).
    gender = BabyInfo.get_gender()
    birth_date = BabyInfo.get_birth_date()
    weight_entries = _attach_percentiles(weight_entries, gender, birth_date, get_weight_percentiles)
    height_entries = _attach_percentiles(height_entries, gender, birth_date, get_height_percentiles)

    return render_template('trends.html',
                         stats=stats,
                         temp_stats=temp_stats,
                         diaper_stats=diaper_stats,
                         feeding_stats=feeding_stats,
                         illness_stats=illness_stats,
                         weight_entries=weight_entries,
                         height_entries=height_entries,
                         start_date=start_date,
                         end_date=end_date)

