from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.models.models import BabyInfo
from datetime import date
import os
import requests

bp = Blueprint('settings', __name__, url_prefix='/settings')

def get_current_version():
    """Liest die aktuelle Version aus der VERSION-Datei"""
    version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'VERSION')
    try:
        with open(version_file, 'r') as f:
            version = f.read().strip()
            return version
    except (FileNotFoundError, IOError):
        return "v1.0.0"  # Fallback

@bp.route('/')
def settings():
    """Einstellungsseite"""
    baby_name = BabyInfo.get_name()
    baby_birth_date = BabyInfo.get_birth_date()
    baby_age_months = BabyInfo.get_age_months() if baby_birth_date else None
    current_version = get_current_version()
    sleep_meta = BabyInfo.get_sleep_meta_settings()
    
    return render_template(
        'settings.html',
        baby_name=baby_name,
        baby_birth_date=baby_birth_date,
        baby_age_months=baby_age_months,
        current_version=current_version,
        sleep_meta=sleep_meta,
    )

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


@bp.route('/sleep-meta', methods=['POST'])
def update_sleep_meta():
    """Aktualisiert die Schlaf-Meta-Einstellungen (Qualität & Ort)"""
    quality_text = request.form.get('sleep_quality_options', '')
    location_text = request.form.get('sleep_location_options', '')
    default_quality = request.form.get('default_sleep_quality', '').strip()
    default_location = request.form.get('default_sleep_location', '').strip()
    
    qualities = [line.strip() for line in quality_text.splitlines() if line.strip()]
    locations = [line.strip() for line in location_text.splitlines() if line.strip()]
    
    BabyInfo.set_sleep_meta_settings(qualities, locations, default_quality, default_location)
    
    flash('Schlaf-Einstellungen gespeichert', 'success')
    return redirect(url_for('settings.settings'))

@bp.route('/check-version')
def check_version():
    """Prüft ob eine neuere Version auf Docker Hub verfügbar ist"""
    try:
        current_version = get_current_version()
        docker_user = "sleepwalker86"
        image_name = "mybaby"
        
        # Docker Hub API v2: Hole alle Tags
        api_url = f"https://hub.docker.com/v2/repositories/{docker_user}/{image_name}/tags"
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        tags = data.get('results', [])
        
        # Finde die neueste Version (sortiere nach Tag-Namen, ignoriere 'latest')
        version_tags = [tag['name'] for tag in tags if tag['name'].startswith('v') and tag['name'] != 'latest']
        
        if not version_tags:
            return jsonify({
                'success': False,
                'message': 'Keine Versionen gefunden',
                'current_version': current_version
            })
        
        # Sortiere Versionen (einfache String-Sortierung sollte für semantische Versionen funktionieren)
        # Für bessere Sortierung könnte man eine semantische Version-Bibliothek verwenden
        version_tags.sort(reverse=True)
        latest_version = version_tags[0]
        
        # Vergleiche Versionen (einfacher String-Vergleich)
        is_update_available = latest_version != current_version
        
        return jsonify({
            'success': True,
            'current_version': current_version,
            'latest_version': latest_version,
            'update_available': is_update_available
        })
        
    except requests.RequestException as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Abrufen der Version: {str(e)}',
            'current_version': get_current_version()
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Unerwarteter Fehler: {str(e)}',
            'current_version': get_current_version()
        }), 500
