from flask import Blueprint, render_template, request
from app.models.models import Sleep, Temperature, Diaper, Feeding
from datetime import datetime, date, timedelta

bp = Blueprint('trends', __name__, url_prefix='/trends')

def format_time(hours):
    """Formatiert Stunden in HH:MM Format"""
    if hours is None or hours == 0:
        return "00:00"
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h:02d}:{m:02d}"

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
    
    return render_template('trends.html',
                         stats=stats,
                         temp_stats=temp_stats,
                         diaper_stats=diaper_stats,
                         feeding_stats=feeding_stats,
                         start_date=start_date,
                         end_date=end_date)

