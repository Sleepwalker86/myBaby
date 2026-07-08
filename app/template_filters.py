"""Jinja2-Template-Filter, zentral definiert und einmalig in create_app() registriert.

Vorher waren diese Filter wortgleich in app/routes/main.py und app/routes/entries.py
dupliziert (Issue #48), was dazu führte, dass der zuletzt registrierte Blueprint die
Filterfunktion des anderen überschrieb und der head_circumference-Zweig in main.py fehlte.
"""
from datetime import datetime

from app.i18n import _
from app.timezone import to_berlin


def translate_entry_display(entry):
    """Übersetzt die display-Eigenschaft eines Eintrags basierend auf seiner Kategorie"""
    if not entry:
        return ""

    category = entry.get('category', '')

    if category == 'sleep':
        sleep_type = entry.get('type', '')
        if sleep_type == 'night':
            return _('entries.night_sleep')
        else:
            return _('entries.nap')
    elif category == 'night_waking':
        return _('entries.night_waking')
    elif category == 'feeding':
        side = entry.get('side', '').lower()
        if side == 'left' or side == 'links':
            return _('entries.feeding_left')
        else:
            return _('entries.feeding_right')
    elif category == 'bottle':
        amount = entry.get('amount', 0)
        return _('bottle.title') + f" ({amount} ml)"
    elif category == 'porridge':
        amount = entry.get('amount', 0)
        food = entry.get('food', '')
        label = _('porridge.title') + f" ({amount} g)"
        if food:
            label += f' – {food}'
        return label
    elif category == 'diaper':
        diaper_type = entry.get('type', '')
        if diaper_type == 'nass':
            return _('entries.diaper_wet')
        elif diaper_type == 'groß':
            return _('entries.diaper_solid')
        else:
            return _('entries.diaper_both')
    elif category == 'temperature':
        value = entry.get('value', 0)
        return _('entries.temperature') + f" ({value}°C)"
    elif category == 'medicine':
        name = entry.get('name', '')
        dose = entry.get('dose', '')
        return _('entries.medicine') + f" ({name}, {dose})"
    elif category == 'weight':
        weight_kg = entry.get('weight_kg', 0)
        return _('weight.title') + f" ({weight_kg} kg)"
    elif category == 'height':
        height_cm = entry.get('height_cm', 0)
        return _('height.title') + f" ({height_cm} cm)"
    elif category == 'head_circumference':
        head_circumference_cm = entry.get('head_circumference_cm', 0)
        return _('head.title') + f" ({head_circumference_cm} cm)"

    # Fallback: Original display verwenden
    return entry.get('display', '')


def format_datetime_de(value):
    """Formatiert einen ISO-Datetime-String ins deutsche Format DD.MM.YYYY HH:MM"""
    if not value:
        return ""
    try:
        dt_local = to_berlin(value).replace(tzinfo=None)
        return dt_local.strftime('%d.%m.%Y %H:%M')
    except (ValueError, AttributeError):
        return value


def calculate_duration(start_time, end_time):
    """Berechnet die Dauer zwischen zwei Zeitstempeln und gibt sie als 'Xh Ym' zurück"""
    if not start_time or not end_time:
        return ""
    try:
        start_dt = to_berlin(start_time)
        end_dt = to_berlin(end_time)

        duration = end_dt - start_dt
        total_seconds = int(duration.total_seconds())

        if total_seconds < 0:
            return ""

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return "< 1m"
    except (ValueError, AttributeError, TypeError):
        return ""


def register_template_filters(app):
    """Registriert alle gemeinsamen Template-Filter genau einmal auf App-Ebene."""
    app.template_filter('translate_entry_display')(translate_entry_display)
    app.template_filter('format_datetime_de')(format_datetime_de)
    app.template_filter('calculate_duration')(calculate_duration)
