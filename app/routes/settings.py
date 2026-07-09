from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, Response, current_app
from app.models.models import BabyInfo, Weight, Height, Sleep, Feeding, Diaper, Temperature
from app.models.database import get_db, get_database_path
from app.i18n import _
from datetime import date, datetime, timedelta
from fpdf import FPDF
from fpdf.enums import XPos, YPos
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
    baby_gender = BabyInfo.get_gender()
    current_version = get_current_version()
    sleep_meta = BabyInfo.get_sleep_meta_settings()
    show_audio_player = BabyInfo.get_show_audio_player()
    report_end_date = date.today().isoformat()
    report_start_date = (date.today() - timedelta(days=30)).isoformat()

    return render_template(
        'settings.html',
        baby_name=baby_name,
        baby_birth_date=baby_birth_date,
        baby_age_months=baby_age_months,
        baby_gender=baby_gender,
        current_version=current_version,
        sleep_meta=sleep_meta,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        show_audio_player=show_audio_player,
    )

@bp.route('/update', methods=['POST'])
def update_settings():
    """Aktualisiert die Einstellungen"""
    name = request.form.get('name', '').strip()
    birth_date_str = request.form.get('birth_date', '').strip()
    gender = request.form.get('gender', '').strip()

    # Validiere und setze Geburtsdatum
    birth_date = None
    if birth_date_str:
        try:
            birth_date = date.fromisoformat(birth_date_str)
        except ValueError:
            flash('Ungültiges Datumsformat', 'error')
            return redirect(url_for('settings.settings'))

    if gender not in ('m', 'f'):
        gender = ''  # zurücksetzen auf "nicht angegeben"

    # Setze Name, Geburtsdatum und/oder Geschlecht
    BabyInfo.set_baby_info(name=name if name else None, birth_date=birth_date, gender=gender)

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


def _build_backup_snapshot(db):
    """Baut ein vollständiges Backup-Dict aus allen Tabellen"""
    def rows_to_list(rows):
        return [dict(r) for r in rows]

    return {
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


@bp.route('/export/backup')
def export_backup():
    """Erstellt ein vollständiges JSON-Backup aller Daten"""
    db = get_db()
    backup = _build_backup_snapshot(db)

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

RESTORE_POINTS_KEEP = 5  # Anzahl der aufbewahrten automatischen Sicherungspunkte


def _create_restore_point(db):
    """Erstellt vor einem Restore automatisch einen internen Sicherungspunkt der aktuellen Daten,
    damit ein fehlerhafter Restore rückgängig gemacht werden kann. Rotiert alte Sicherungspunkte."""
    restore_points_dir = os.path.join(os.path.dirname(get_database_path()), 'restore_points')
    os.makedirs(restore_points_dir, exist_ok=True)

    snapshot = _build_backup_snapshot(db)
    filename = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    with open(os.path.join(restore_points_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, ensure_ascii=False)

    existing = sorted(f for f in os.listdir(restore_points_dir)
                       if f.startswith('pre_restore_') and f.endswith('.json'))
    for old_file in existing[:-RESTORE_POINTS_KEEP]:
        try:
            os.remove(os.path.join(restore_points_dir, old_file))
        except OSError:
            pass


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

    missing_tables = [t for t in BACKUP_TABLES if t not in backup]
    if missing_tables:
        flash(f"{_('settings.restore_error_missing_tables')}: {', '.join(missing_tables)}", 'error')
        return redirect(url_for('settings.settings'))

    db = get_db()

    tables_losing_data = [
        table for table in BACKUP_TABLES
        if not backup.get(table) and db.execute(f'SELECT 1 FROM {table} LIMIT 1').fetchone()
    ]
    if tables_losing_data and not request.form.get('confirm_empty_tables'):
        flash(f"{_('settings.restore_error_empty_tables')}: {', '.join(tables_losing_data)}", 'error')
        return redirect(url_for('settings.settings'))

    try:
        _create_restore_point(db)
        for table in BACKUP_TABLES:
            _restore_table(db, table, backup.get(table, []))
        db.commit()
    except Exception:
        db.rollback()
        current_app.logger.exception("Fehler beim Wiederherstellen des Backups")
        flash(_('settings.restore_error_db'), 'error')
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
        
    except requests.RequestException:
        current_app.logger.exception("Fehler beim Abrufen der Versionsinformationen von Docker Hub")
        return jsonify({
            'success': False,
            'message': _('settings.unknown_error'),
            'current_version': get_current_version()
        }), 500
    except Exception:
        current_app.logger.exception("Unerwarteter Fehler bei der Versionsprüfung")
        return jsonify({
            'success': False,
            'message': _('settings.unknown_error'),
            'current_version': get_current_version()
        }), 500


def _fmt_date(d):
    return d.strftime('%d.%m.%Y')


def _fmt_ts(ts_str):
    """Formatiert einen ISO-Zeitstempel-String als 'DD.MM.YYYY HH:MM'"""
    try:
        dt = datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M')
    except (ValueError, TypeError):
        return str(ts_str)


def _format_hours_as_time(hours):
    """Formatiert eine Dezimalstunde (z.B. 7.5) als HH:MM"""
    if not hours:
        return '-'
    h = int(hours)
    m = int(round((hours - h) * 60))
    return f"{h:02d}:{m:02d}"


def _build_medical_report_pdf(ctx):
    """Baut den Arztbericht als PDF aus vorbereiteten Statistik-/Rohdaten (rein deutschsprachig,
    da für den ersten Wurf keine Übersetzung des PDF-Inhalts gefordert ist - nur die UI drumherum)."""
    pdf = FPDF(format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def line(text, size=11, style=''):
        pdf.set_font('Helvetica', style, size)
        pdf.cell(0, 6, text=text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def section_title(text):
        pdf.ln(3)
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 8, text=text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        pdf.ln(1)

    def kv(label, value):
        line(f"{label}: {value}")

    line('myBaby - Arztbericht', size=18, style='B')
    line(f"Baby: {ctx['baby_name'] or '-'}")
    if ctx['baby_age_months'] is not None:
        line(f"Alter: {ctx['baby_age_months']} Monate")
    line(f"Zeitraum: {_fmt_date(ctx['start_date'])} - {_fmt_date(ctx['end_date'])}")
    line(f"Erstellt am: {_fmt_date(date.today())}")

    # Wachstum
    section_title('Wachstum')
    weight_entries = ctx['weight_entries']
    height_entries = ctx['height_entries']
    if weight_entries:
        first_w, last_w = weight_entries[0], weight_entries[-1]
        delta_w = last_w['weight_kg'] - first_w['weight_kg']
        kv('Gewicht (aktuell)', f"{last_w['weight_kg']:.2f} kg (am {_fmt_ts(last_w['timestamp'])})")
        kv('Veränderung im Zeitraum', f"{delta_w:+.2f} kg (Start: {first_w['weight_kg']:.2f} kg)")
    else:
        kv('Gewicht', 'Keine Daten im Zeitraum')
    if height_entries:
        first_h, last_h = height_entries[0], height_entries[-1]
        delta_h = last_h['height_cm'] - first_h['height_cm']
        kv('Größe (aktuell)', f"{last_h['height_cm']:.1f} cm (am {_fmt_ts(last_h['timestamp'])})")
        kv('Veränderung im Zeitraum', f"{delta_h:+.1f} cm (Start: {first_h['height_cm']:.1f} cm)")
    else:
        kv('Größe', 'Keine Daten im Zeitraum')

    # Schlaf
    section_title('Schlaf')
    s = ctx['sleep_stats']
    if s['total_days'] > 0:
        kv('Ø Schlaf pro Tag', f"{s['avg_daily_sleep']} h (über {s['total_days']} Tage)")
        kv('Nickerchen / Nachtschlaf', f"{s['nap_hours']} h / {s['night_hours']} h")
        kv('Ø Aufwachzeit', _format_hours_as_time(s['avg_wake_time']) if s['wake_times'] else '-')
        kv('Ø Einschlafzeit', _format_hours_as_time(s['avg_sleep_time']) if s['sleep_times'] else '-')
    else:
        kv('Schlaf', 'Keine Daten im Zeitraum')

    # Fütterung
    section_title('Fütterung')
    f = ctx['feeding_stats']
    kv('Stillmahlzeiten', f"{f['total_count']} gesamt, Ø {f['avg_count']}/Tag")
    if ctx['bottle_count'] > 0:
        kv('Flasche', f"{ctx['bottle_count']} Mahlzeiten, {ctx['bottle_total_ml']} ml gesamt, "
                       f"Ø {ctx['bottle_avg_ml_per_day']} ml/Tag")
    else:
        kv('Flasche', 'Keine Einträge im Zeitraum')

    # Windel
    section_title('Windel')
    d = ctx['diaper_stats']
    kv('Gesamt', f"{d['total_count']} (Ø {d['avg_total']}/Tag)")
    kv('Nass / Groß / Beides', f"{d['nass_count']} / {d['groß_count']} / {d['beides_count']}")

    # Temperatur
    section_title('Temperatur')
    t = ctx['temp_stats']
    if t['count'] > 0:
        kv('Min / Ø / Max', f"{t['min_temp']} / {t['avg_temp']} / {t['max_temp']} °C")
        high_temps = [x for x in t['all_temps'] if x['value'] > 38.0]
        if high_temps:
            line('Erhöhte Werte (> 38.0 °C):')
            for x in high_temps:
                line(f"   {_fmt_ts(x['timestamp'])}: {x['value']} °C")
        else:
            kv('Erhöhte Werte (> 38.0 °C)', 'Keine')
    else:
        kv('Temperatur', 'Keine Messungen im Zeitraum')

    # Erkrankungsphasen
    section_title('Erkrankungsphasen')
    illness_rows = ctx['illness_rows']
    if illness_rows:
        for ill in illness_rows:
            end_txt = _fmt_ts(ill['end_time']) if ill['end_time'] else 'andauernd'
            line(f"{ill['type']}: {_fmt_ts(ill['start_time'])} - {end_txt}", style='B')
            if ill.get('symptoms'):
                pdf.set_font('Helvetica', '', 11)
                pdf.multi_cell(0, 6, text=f"   Symptome: {ill['symptoms']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            if ill.get('notes'):
                pdf.set_font('Helvetica', '', 11)
                pdf.multi_cell(0, 6, text=f"   Notizen: {ill['notes']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        kv('Erkrankungsphasen', 'Keine im Zeitraum')

    # Medikamente
    section_title('Medikamente')
    medicine_rows = ctx['medicine_rows']
    if medicine_rows:
        for m in medicine_rows:
            line(f"{_fmt_ts(m['timestamp'])}: {m['name']} - {m['dose']}")
    else:
        kv('Medikamente', 'Keine im Zeitraum')

    return pdf


@bp.route('/export/report')
def export_report():
    """Erstellt einen für Menschen lesbaren PDF-Arztbericht für einen wählbaren Zeitraum.
    Ergänzt export_csv/export_backup um eine dritte, zusammenfassende Export-Variante."""
    end_date_obj = date.today()
    start_date_obj = end_date_obj - timedelta(days=30)

    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()
    if start_date_str:
        try:
            start_date_obj = date.fromisoformat(start_date_str)
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date_obj = date.fromisoformat(end_date_str)
        except ValueError:
            pass
    if start_date_obj > end_date_obj:
        start_date_obj, end_date_obj = end_date_obj, start_date_obj

    db = get_db()
    range_start_str = datetime.combine(start_date_obj, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%S')
    range_end_str = datetime.combine(end_date_obj, datetime.max.time().replace(hour=23, minute=59, second=59)).strftime('%Y-%m-%dT%H:%M:%S')

    illness_rows = [dict(r) for r in db.execute(
        '''SELECT * FROM illness WHERE start_time <= ? AND (end_time IS NULL OR end_time >= ?)
           ORDER BY start_time''',
        (range_end_str, range_start_str)
    ).fetchall()]

    medicine_rows = [dict(r) for r in db.execute(
        'SELECT * FROM medicine WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp',
        (range_start_str, range_end_str)
    ).fetchall()]

    bottle_rows = db.execute(
        'SELECT amount FROM bottle WHERE timestamp >= ? AND timestamp <= ?',
        (range_start_str, range_end_str)
    ).fetchall()
    bottle_total_ml = sum(r['amount'] for r in bottle_rows)
    bottle_count = len(bottle_rows)
    days_count = (end_date_obj - start_date_obj).days + 1
    bottle_avg_ml_per_day = round(bottle_total_ml / days_count, 1) if days_count > 0 else 0

    ctx = {
        'baby_name': BabyInfo.get_name(),
        'baby_age_months': BabyInfo.get_age_months() if BabyInfo.get_birth_date() else None,
        'start_date': start_date_obj,
        'end_date': end_date_obj,
        'weight_entries': Weight.get_in_range(start_date_obj, end_date_obj),
        'height_entries': Height.get_in_range(start_date_obj, end_date_obj),
        'sleep_stats': Sleep.get_sleep_statistics(start_date_obj, end_date_obj),
        'feeding_stats': Feeding.get_feeding_statistics(start_date_obj, end_date_obj),
        'diaper_stats': Diaper.get_diaper_statistics(start_date_obj, end_date_obj),
        'temp_stats': Temperature.get_temperature_statistics(start_date_obj, end_date_obj),
        'illness_rows': illness_rows,
        'medicine_rows': medicine_rows,
        'bottle_count': bottle_count,
        'bottle_total_ml': bottle_total_ml,
        'bottle_avg_ml_per_day': bottle_avg_ml_per_day,
    }

    pdf = _build_medical_report_pdf(ctx)
    filename = f"mybaby_bericht_{start_date_obj.isoformat()}_{end_date_obj.isoformat()}.pdf"
    return Response(
        bytes(pdf.output()),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
