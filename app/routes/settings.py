from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, Response
from app.models.models import BabyInfo
from app.models.database import get_db
from app.i18n import _
from datetime import date, datetime
import os
import csv
import io
import json
import requests
import time

bp = Blueprint('settings', __name__, url_prefix='/settings')

_version_cache = {'data': None, 'ts': 0}
_VERSION_CACHE_TTL = 3600  # 1 Stunde

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
    show_audio_player = BabyInfo.get_show_audio_player()

    return render_template(
        'settings.html',
        baby_name=baby_name,
        baby_birth_date=baby_birth_date,
        baby_age_months=baby_age_months,
        current_version=current_version,
        sleep_meta=sleep_meta,
        show_audio_player=show_audio_player,
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


@bp.route('/audio-player', methods=['POST'])
def update_audio_player():
    """Aktualisiert die Audio-Player Sichtbarkeitseinstellung"""
    show = request.form.get('show_audio_player') == '1'
    BabyInfo.set_show_audio_player(show)
    flash(_('settings.saved'), 'success')
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

def _g(row, key, default=''):
    """sqlite3.Row als dict lesen (unterstützt kein .get())"""
    d = dict(row)
    return d.get(key, default)


@bp.route('/export/csv')
def export_csv():
    """Exportiert alle Einträge als CSV"""
    db = get_db()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['category', 'id', 'timestamp', 'end_time', 'type', 'amount',
                     'amount_g', 'food', 'side', 'value', 'name', 'dose',
                     'weight_kg', 'height_cm', 'notes', 'sleep_quality', 'sleep_location',
                     'head_circumference_cm'])

    # Schlaf (start_time = timestamp)
    for r in db.execute('SELECT * FROM sleep ORDER BY start_time').fetchall():
        writer.writerow(['sleep', r['id'], r['start_time'], _g(r, 'end_time'), r['type'],
                         '', '', '', '', '', '', '', '', '', _g(r, 'sleep_comment'),
                         _g(r, 'sleep_quality'), _g(r, 'sleep_location'), ''])

    # Stillen (timestamp, side, end_time)
    for r in db.execute('SELECT * FROM feeding ORDER BY timestamp').fetchall():
        writer.writerow(['feeding', r['id'], r['timestamp'], _g(r, 'end_time'), '',
                         '', '', '', r['side'], '', '', '', '', '', '', '', '', ''])

    # Flasche
    for r in db.execute('SELECT * FROM bottle ORDER BY timestamp').fetchall():
        writer.writerow(['bottle', r['id'], r['timestamp'], '', '',
                         r['amount'], '', '', '', '', '', '', '', '', _g(r, 'notes'), '', '', ''])

    # Windel
    for r in db.execute('SELECT * FROM diaper ORDER BY timestamp').fetchall():
        writer.writerow(['diaper', r['id'], r['timestamp'], '', r['type'],
                         '', '', '', '', '', '', '', '', '', '', '', '', ''])

    # Temperatur
    for r in db.execute('SELECT * FROM temperature ORDER BY timestamp').fetchall():
        writer.writerow(['temperature', r['id'], r['timestamp'], '', '',
                         '', '', '', '', r['value'], '', '', '', '', '', '', '', ''])

    # Medizin
    for r in db.execute('SELECT * FROM medicine ORDER BY timestamp').fetchall():
        writer.writerow(['medicine', r['id'], r['timestamp'], '', '',
                         '', '', '', '', '', r['name'], r['dose'], '', '', '', '', '', ''])

    # Brei
    for r in db.execute('SELECT * FROM porridge ORDER BY timestamp').fetchall():
        writer.writerow(['porridge', r['id'], r['timestamp'], '', '',
                         '', r['amount'], _g(r, 'food'), '', '', '', '', '', '', _g(r, 'notes'), '', '', ''])

    # Gewicht
    for r in db.execute('SELECT * FROM weight ORDER BY timestamp').fetchall():
        writer.writerow(['weight', r['id'], r['timestamp'], '', '',
                         '', '', '', '', '', '', '', r['weight_kg'], '', _g(r, 'notes'), '', '', ''])

    # Größe
    for r in db.execute('SELECT * FROM height ORDER BY timestamp').fetchall():
        writer.writerow(['height', r['id'], r['timestamp'], '', '',
                         '', '', '', '', '', '', '', '', r['height_cm'], _g(r, 'notes'), '', '', ''])

    # Kopfumfang
    for r in db.execute('SELECT * FROM head_circumference ORDER BY timestamp').fetchall():
        writer.writerow(['head_circumference', r['id'], r['timestamp'], '', '',
                         '', '', '', '', '', '', '', '', '', _g(r, 'notes'), '', '', r['head_circumference_cm']])

    # Erkrankungen
    for r in db.execute('SELECT * FROM illness ORDER BY start_time').fetchall():
        writer.writerow(['illness', r['id'], r['start_time'], _g(r, 'end_time'), _g(r, 'type'),
                         '', '', '', '', '', '', '', '', '', _g(r, 'notes'), '', '', ''])

    # Nächtliches Aufwachen
    for r in db.execute('SELECT * FROM night_waking ORDER BY start_time').fetchall():
        writer.writerow(['night_waking', r['id'], r['start_time'], _g(r, 'end_time'), '',
                         '', '', '', '', '', '', '', '', '', '', '', '', ''])

    filename = f"mybaby_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        '﻿' + output.getvalue(),  # BOM für Excel-Kompatibilität
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@bp.route('/export/backup')
def export_backup():
    """Erstellt ein vollständiges JSON-Backup aller Daten"""
    db = get_db()

    def rows_to_list(rows):
        return [dict(r) for r in rows]

    backup = {
        'exported_at': datetime.now().isoformat(),
        'version': get_current_version(),
        'baby_info': rows_to_list(db.execute('SELECT * FROM baby_info').fetchall()),
        'sleep': rows_to_list(db.execute('SELECT * FROM sleep ORDER BY start_time').fetchall()),
        'feeding': rows_to_list(db.execute('SELECT * FROM feeding ORDER BY timestamp').fetchall()),
        'bottle': rows_to_list(db.execute('SELECT * FROM bottle ORDER BY timestamp').fetchall()),
        'diaper': rows_to_list(db.execute('SELECT * FROM diaper ORDER BY timestamp').fetchall()),
        'temperature': rows_to_list(db.execute('SELECT * FROM temperature ORDER BY timestamp').fetchall()),
        'medicine': rows_to_list(db.execute('SELECT * FROM medicine ORDER BY timestamp').fetchall()),
        'porridge': rows_to_list(db.execute('SELECT * FROM porridge ORDER BY timestamp').fetchall()),
        'weight': rows_to_list(db.execute('SELECT * FROM weight ORDER BY timestamp').fetchall()),
        'height': rows_to_list(db.execute('SELECT * FROM height ORDER BY timestamp').fetchall()),
        'head_circumference': rows_to_list(db.execute('SELECT * FROM head_circumference ORDER BY timestamp').fetchall()),
        'illness': rows_to_list(db.execute('SELECT * FROM illness ORDER BY start_time').fetchall()),
        'night_waking': rows_to_list(db.execute('SELECT * FROM night_waking ORDER BY start_time').fetchall()),
    }

    filename = f"mybaby_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return Response(
        json.dumps(backup, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


def _restore_table(db, table_name, rows):
    """Löscht Tabelle und füllt sie mit Backup-Daten. Nur vorhandene Spalten werden eingefügt."""
    db.execute(f'DELETE FROM {table_name}')
    if not rows:
        return
    existing_cols = {row[1] for row in db.execute(f'PRAGMA table_info({table_name})').fetchall()}
    for row in rows:
        filtered = {k: v for k, v in row.items() if k in existing_cols}
        if not filtered:
            continue
        cols = ', '.join(f'"{c}"' for c in filtered.keys())
        placeholders = ', '.join(['?' for _ in filtered])
        db.execute(f'INSERT INTO {table_name} ({cols}) VALUES ({placeholders})', list(filtered.values()))


BACKUP_TABLES = ['sleep', 'feeding', 'bottle', 'diaper', 'temperature', 'medicine',
                 'porridge', 'weight', 'height', 'head_circumference', 'illness', 'night_waking', 'baby_info']


@bp.route('/restore', methods=['POST'])
def restore_backup():
    """Stellt alle Daten aus einem JSON-Backup wieder her"""
    if 'backup_file' not in request.files or request.files['backup_file'].filename == '':
        flash(_('settings.restore_error_no_file'), 'error')
        return redirect(url_for('settings.settings'))

    if not request.form.get('confirm_restore'):
        flash(_('settings.restore_error_no_confirm'), 'error')
        return redirect(url_for('settings.settings'))

    file = request.files['backup_file']
    if not file.filename.lower().endswith('.json'):
        flash(_('settings.restore_error_invalid_format'), 'error')
        return redirect(url_for('settings.settings'))

    try:
        content = file.read(10 * 1024 * 1024)  # max 10 MB
        backup = json.loads(content.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        flash(_('settings.restore_error_invalid_json'), 'error')
        return redirect(url_for('settings.settings'))

    if not isinstance(backup, dict) or 'exported_at' not in backup:
        flash(_('settings.restore_error_invalid_format'), 'error')
        return redirect(url_for('settings.settings'))

    db = get_db()
    try:
        for table in BACKUP_TABLES:
            _restore_table(db, table, backup.get(table, []))
        db.commit()
    except Exception as e:
        db.rollback()
        flash(f"{_('settings.restore_error_db')}: {e}", 'error')
        return redirect(url_for('settings.settings'))

    flash(_('settings.restore_success'), 'success')
    return redirect(url_for('settings.settings'))


@bp.route('/check-version')
def check_version():
    """Prüft ob eine neuere Version auf Docker Hub verfügbar ist"""
    if _version_cache['data'] and (time.time() - _version_cache['ts']) < _VERSION_CACHE_TTL:
        return jsonify(_version_cache['data'])
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
        
        def parse_version(v):
            try:
                return tuple(int(x) for x in v.lstrip('v').split('.'))
            except ValueError:
                return (0,)

        version_tags.sort(key=parse_version, reverse=True)
        latest_version = version_tags[0]

        current_tuple = parse_version(current_version)
        latest_tuple = parse_version(latest_version)
        is_update_available = latest_tuple > current_tuple
        
        result = {
            'success': True,
            'current_version': current_version,
            'latest_version': latest_version,
            'update_available': is_update_available
        }
        _version_cache['data'] = result
        _version_cache['ts'] = time.time()
        return jsonify(result)
        
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
