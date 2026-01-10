"""Datenmodelle für die Baby-Tracking App"""
from app.models.database import get_db
from datetime import datetime, date, timedelta
import pytz

tz_berlin = pytz.timezone('Europe/Berlin')

class Sleep:
    """Schlaf-Tracking"""
    @staticmethod
    def create_nap(start_time, end_time=None):
        """Erstellt ein Nickerchen"""
        db = get_db()
        cursor = db.execute(
            'INSERT INTO sleep (type, start_time, end_time) VALUES (?, ?, ?)',
            ('nap', start_time, end_time)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def create_night_sleep(start_time, end_time=None):
        """Erstellt einen Nachtschlaf"""
        db = get_db()
        cursor = db.execute(
            'INSERT INTO sleep (type, start_time, end_time) VALUES (?, ?, ?)',
            ('night', start_time, end_time)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def end_sleep(sleep_id, end_time):
        """Beendet einen Schlaf"""
        db = get_db()
        db.execute(
            'UPDATE sleep SET end_time = ? WHERE id = ?',
            (end_time, sleep_id)
        )
        db.commit()
    
    @staticmethod
    def get_active_sleep():
        """Gibt den aktiven Schlaf zurück (falls vorhanden)"""
        db = get_db()
        row = db.execute(
            'SELECT * FROM sleep WHERE end_time IS NULL ORDER BY start_time DESC LIMIT 1'
        ).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def get_today_sleep_duration(selected_date=None):
        """Berechnet die Schlafdauer für einen bestimmten Tag in Stunden"""
        db = get_db()
        
        # Normalisiere selected_date zu einem date-Objekt
        if selected_date is None:
            selected_date = date.today()
        elif isinstance(selected_date, str):
            selected_date = date.fromisoformat(selected_date)
        elif not isinstance(selected_date, date):
            selected_date = date.fromisoformat(str(selected_date))
        
        total_seconds = 0.0
        
        # Hole ALLE beendeten Schlaf-Einträge
        all_rows = db.execute(
            '''SELECT type, start_time, end_time FROM sleep 
               WHERE end_time IS NOT NULL'''
        ).fetchall()
        
        # Hilfsfunktion zum Parsen von Zeitstempeln - EINFACH und DIREKT
        def parse_to_berlin(dt_str):
            """Parst einen Zeitstempel-String und konvertiert ihn zur Berliner Zeitzone"""
            if not dt_str:
                return None
            
            dt_str = str(dt_str).strip()
            
            # Format in DB: 2026-01-02T19:59 (ohne Sekunden, ohne Zeitzone)
            # Entferne Zeitzone-Info falls vorhanden
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1]
            elif '+' in dt_str:
                plus_pos = dt_str.rfind('+')
                if plus_pos > 10:
                    dt_str = dt_str[:plus_pos]
            elif dt_str.count('-') > 2:
                # Prüfe ob letztes '-' eine Zeitzone ist (Format: -HH:MM)
                parts = dt_str.rsplit('-', 1)
                if len(parts) == 2 and ':' in parts[1] and len(parts[1]) <= 6:
                    dt_str = parts[0]
            
            # Entferne Mikrosekunden
            if '.' in dt_str:
                dt_str = dt_str.split('.')[0]
            
            # Parse - versuche zuerst mit Sekunden, dann ohne
            dt = None
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M']:
                try:
                    dt = datetime.strptime(dt_str, fmt)
                    break
                except ValueError:
                    continue
            
            if dt is None:
                return None
            
            # Konvertiere zu Berliner Zeitzone (immer, da DB keine Zeitzone hat)
            dt = tz_berlin.localize(dt)
            
            return dt
        
        # Verarbeite jeden Eintrag
        for row in all_rows:
            try:
                # Hole Spalten - verwende direkten Zugriff
                sleep_type = str(row['type']).strip()
                start_str = str(row['start_time']).strip()
                end_str = str(row['end_time']).strip()
                
                # Parse Zeitstempel
                start_dt = parse_to_berlin(start_str)
                end_dt = parse_to_berlin(end_str)
                
                if start_dt is None or end_dt is None:
                    # Wenn Parsing fehlschlägt, versuche es mit einem einfacheren Ansatz
                    # Manchmal sind die Werte bereits datetime-Objekte
                    if isinstance(row['start_time'], datetime):
                        start_dt = row['start_time']
                        if start_dt.tzinfo is None:
                            start_dt = tz_berlin.localize(start_dt)
                        else:
                            start_dt = start_dt.astimezone(tz_berlin)
                    if isinstance(row['end_time'], datetime):
                        end_dt = row['end_time']
                        if end_dt.tzinfo is None:
                            end_dt = tz_berlin.localize(end_dt)
                        else:
                            end_dt = end_dt.astimezone(tz_berlin)
                    
                    if start_dt is None or end_dt is None:
                        continue
                
                # Hole Datum von Start und Ende
                start_date = start_dt.date()
                end_date = end_dt.date()
                
                # Prüfe ob dieser Eintrag für den ausgewählten Tag relevant ist
                # WICHTIG: Eintrag ist relevant, wenn er am ausgewählten Tag ENDET
                if end_date == selected_date:
                    # Für alle Schlaf-Einträge (Nickerchen und Nachtschlaf): Gesamte Dauer von Start bis Ende zählen
                    duration_seconds = (end_dt - start_dt).total_seconds()
                    total_seconds += duration_seconds
                            
            except Exception as e:
                # Bei Fehler: Weiter mit nächstem Eintrag
                continue
        
        # Aktive Schlaf-Einträge (noch nicht beendet) - nur für heute relevant
        if selected_date == date.today():
            active_sleep_rows = db.execute(
                '''SELECT type, start_time FROM sleep 
                   WHERE end_time IS NULL'''
            ).fetchall()
            
            day_start_dt = tz_berlin.localize(datetime.combine(selected_date, datetime.min.time()))
            day_end_dt = tz_berlin.localize(datetime.combine(selected_date, datetime.max.time().replace(hour=23, minute=59, second=59)))
            
            for row in active_sleep_rows:
                try:
                    try:
                        sleep_type = row['type']
                    except (KeyError, IndexError):
                        sleep_type = 'night'
                    
                    start_dt = parse_to_berlin(row['start_time'])
                    if start_dt is None:
                        continue
                    
                    start_date = start_dt.date()
                    
                    # Prüfe ob der aktive Schlaf für den ausgewählten Tag relevant ist
                    if start_date <= selected_date:
                        # Für aktive Schlaf-Einträge: Bis zum aktuellen Zeitpunkt oder Tagesende zählen
                        now = datetime.now(tz_berlin)
                        end_time = min(day_end_dt, now)
                        
                        # Für aktive Schlaf-Einträge: Nur die Zeit vom Start bis jetzt zählen
                        # Prüfe ob der Start am ausgewählten Tag liegt
                        if start_date == selected_date:
                            # Gestartet am ausgewählten Tag: Zeit vom Start bis jetzt zählen
                            if end_time > start_dt:
                                duration_seconds = (end_time - start_dt).total_seconds()
                                total_seconds += duration_seconds
                        elif start_date < selected_date and sleep_type == 'night':
                            # Nachtschlaf gestartet am Vortag: Gesamte Dauer vom Start bis jetzt zählen
                            if end_time > start_dt:
                                duration_seconds = (end_time - start_dt).total_seconds()
                                total_seconds += duration_seconds
                except Exception:
                    continue
        
        return round(total_seconds / 3600, 1) if total_seconds > 0 else 0.0
    
    @staticmethod
    def get_by_id(sleep_id):
        """Holt einen Schlaf-Eintrag nach ID"""
        db = get_db()
        row = db.execute('SELECT * FROM sleep WHERE id = ?', (sleep_id,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def update(sleep_id, start_time, end_time=None, sleep_type=None):
        """Aktualisiert einen Schlaf-Eintrag"""
        db = get_db()
        if sleep_type:
            db.execute(
                'UPDATE sleep SET type = ?, start_time = ?, end_time = ? WHERE id = ?',
                (sleep_type, start_time, end_time, sleep_id)
            )
        else:
            db.execute(
                'UPDATE sleep SET start_time = ?, end_time = ? WHERE id = ?',
                (start_time, end_time, sleep_id)
            )
        db.commit()
    
    @staticmethod
    def delete(sleep_id):
        """Löscht einen Schlaf-Eintrag"""
        db = get_db()
        db.execute('DELETE FROM sleep WHERE id = ?', (sleep_id,))
        db.commit()
    
    @staticmethod
    def get_sleep_statistics(start_date, end_date):
        """Gibt Schlaf-Statistiken für einen Zeitraum zurück"""
        db = get_db()
        
        # Alle Schlaf-Einträge, die im Zeitraum gestartet haben
        rows = db.execute(
            '''SELECT type, start_time, end_time FROM sleep 
               WHERE date(start_time) >= ? AND date(start_time) <= ? AND end_time IS NOT NULL
               ORDER BY start_time''',
            (start_date, end_date)
        ).fetchall()
        
        # Schlaf-Einträge, die vor dem Zeitraum gestartet haben, aber im Zeitraum enden
        rows_prev = db.execute(
            '''SELECT type, start_time, end_time FROM sleep 
               WHERE date(start_time) < ? AND date(end_time) >= ? AND date(end_time) <= ? AND end_time IS NOT NULL
               ORDER BY start_time''',
            (start_date, start_date, end_date)
        ).fetchall()
        
        daily_sleep = {}  # {date: total_hours}
        nap_hours = 0
        night_hours = 0
        wake_times = []  # Aufwachzeiten
        sleep_times = []  # Einschlafzeiten
        
        # Verarbeite Einträge, die im Zeitraum gestartet haben
        for row in rows:
            try:
                start = datetime.fromisoformat(row['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(row['end_time'].replace('Z', '+00:00'))
                
                # Konvertiere zu Berliner Zeitzone falls nötig
                if start.tzinfo is None:
                    start = tz_berlin.localize(start.replace(tzinfo=None))
                elif start.tzinfo != tz_berlin:
                    start = start.astimezone(tz_berlin)
                
                if end.tzinfo is None:
                    end = tz_berlin.localize(end.replace(tzinfo=None))
                elif end.tzinfo != tz_berlin:
                    end = end.astimezone(tz_berlin)
                
                # Gesamtdauer berechnen
                duration_hours = (end - start).total_seconds() / 3600
                
                # Bei Nachtschlaf: Gesamte Dauer dem Tag zurechnen, an dem aufgewacht wird
                # Bei Nickerchen: Dauer dem Tag zurechnen, an dem das Nickerchen endet
                if row['type'] == 'night':
                    # Nachtschlaf: Gesamte Dauer dem Aufwach-Tag zurechnen
                    day_key = end.date().isoformat()
                    if start_date <= day_key <= end_date:
                        if day_key not in daily_sleep:
                            daily_sleep[day_key] = 0
                        daily_sleep[day_key] += duration_hours
                else:
                    # Nickerchen: Wenn über Mitternacht, aufteilen (oder auch dem End-Tag zurechnen?)
                    # Für Konsistenz: Auch Nickerchen dem End-Tag zurechnen
                    if start.date() != end.date():
                        # Über Mitternacht: Dem End-Tag zurechnen
                        day_key = end.date().isoformat()
                        if start_date <= day_key <= end_date:
                            if day_key not in daily_sleep:
                                daily_sleep[day_key] = 0
                            daily_sleep[day_key] += duration_hours
                    else:
                        # Innerhalb eines Tages
                        day_key = start.date().isoformat()
                        if start_date <= day_key <= end_date:
                            if day_key not in daily_sleep:
                                daily_sleep[day_key] = 0
                            daily_sleep[day_key] += duration_hours
                
                if row['type'] == 'nap':
                    nap_hours += duration_hours
                else:
                    night_hours += duration_hours
                    # Aufwachzeit und Einschlafzeit: Nur für Nachtschlaf
                    # Aufwachzeit (end_time) - nur wenn im Zeitraum
                    if start_date <= end.date().isoformat() <= end_date:
                        wake_times.append(end.hour + end.minute / 60.0)
                    # Einschlafzeit (start_time) - nur wenn im Zeitraum
                    if start_date <= start.date().isoformat() <= end_date:
                        sleep_times.append(start.hour + start.minute / 60.0)
                
            except (ValueError, AttributeError):
                continue
        
        # Verarbeite Einträge, die vor dem Zeitraum gestartet haben, aber im Zeitraum enden
        for row in rows_prev:
            try:
                start = datetime.fromisoformat(row['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(row['end_time'].replace('Z', '+00:00'))
                
                # Konvertiere zu Berliner Zeitzone falls nötig
                if start.tzinfo is None:
                    start = tz_berlin.localize(start.replace(tzinfo=None))
                elif start.tzinfo != tz_berlin:
                    start = start.astimezone(tz_berlin)
                
                if end.tzinfo is None:
                    end = tz_berlin.localize(end.replace(tzinfo=None))
                elif end.tzinfo != tz_berlin:
                    end = end.astimezone(tz_berlin)
                
                # Gesamtdauer berechnen
                duration_hours = (end - start).total_seconds() / 3600
                
                # Bei Nachtschlaf: Gesamte Dauer dem Aufwach-Tag zurechnen
                # Bei Nickerchen: Auch dem End-Tag zurechnen
                if row['type'] == 'night':
                    # Nachtschlaf: Gesamte Dauer dem Aufwach-Tag zurechnen (auch wenn vor Zeitraum gestartet)
                    day_key = end.date().isoformat()
                    if start_date <= day_key <= end_date:
                        if day_key not in daily_sleep:
                            daily_sleep[day_key] = 0
                        daily_sleep[day_key] += duration_hours
                else:
                    # Nickerchen: Nur der Teil im Zeitraum
                    start_of_period = tz_berlin.localize(datetime.combine(date.fromisoformat(start_date), datetime.min.time()))
                    if start < start_of_period:
                        # Nur der Teil im Zeitraum zählen
                        day_key = end.date().isoformat()
                        if start_date <= day_key <= end_date:
                            day_start = tz_berlin.localize(datetime.combine(end.date(), datetime.min.time()))
                            day_duration = (end - day_start).total_seconds() / 3600
                            if day_key not in daily_sleep:
                                daily_sleep[day_key] = 0
                            daily_sleep[day_key] += day_duration
                    else:
                        # Gesamte Dauer dem End-Tag zurechnen
                        day_key = end.date().isoformat()
                        if start_date <= day_key <= end_date:
                            if day_key not in daily_sleep:
                                daily_sleep[day_key] = 0
                            daily_sleep[day_key] += duration_hours
                
                if row['type'] == 'nap':
                    nap_hours += duration_hours
                else:
                    night_hours += duration_hours
                    # Aufwachzeit: Nur für Nachtschlaf
                    wake_times.append(end.hour + end.minute / 60.0)
                
            except (ValueError, AttributeError):
                continue
        
        # Durchschnitte berechnen
        total_sleep = sum(daily_sleep.values())
        total_days = len(daily_sleep)
        avg_daily_sleep = total_sleep / total_days if total_days > 0 else 0
        avg_wake_time = sum(wake_times) / len(wake_times) if wake_times else 0
        avg_sleep_time = sum(sleep_times) / len(sleep_times) if sleep_times else 0
        
        return {
            'daily_sleep': daily_sleep,  # {date: hours}
            'total_sleep': round(total_sleep, 1),
            'avg_daily_sleep': round(avg_daily_sleep, 1),
            'nap_hours': round(nap_hours, 1),
            'night_hours': round(night_hours, 1),
            'nap_percentage': round(nap_hours / total_sleep * 100, 1) if total_sleep > 0 else 0,
            'night_percentage': round(night_hours / total_sleep * 100, 1) if total_sleep > 0 else 0,
            'wake_times': wake_times,
            'sleep_times': sleep_times,
            'avg_wake_time': round(avg_wake_time, 1),
            'avg_sleep_time': round(avg_sleep_time, 1),
            'total_days': total_days
        }

class Feeding:
    """Stillen-Tracking"""
    @staticmethod
    def create(timestamp, side):
        """Erstellt einen Still-Eintrag"""
        db = get_db()
        cursor = db.execute(
            'INSERT INTO feeding (timestamp, side) VALUES (?, ?)',
            (timestamp, side)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_latest():
        """Gibt die letzte Stillzeit zurück"""
        db = get_db()
        row = db.execute(
            'SELECT * FROM feeding ORDER BY timestamp DESC LIMIT 1'
        ).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def get_by_id(feeding_id):
        """Holt einen Still-Eintrag nach ID"""
        db = get_db()
        row = db.execute('SELECT * FROM feeding WHERE id = ?', (feeding_id,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def update(feeding_id, timestamp, side):
        """Aktualisiert einen Still-Eintrag"""
        db = get_db()
        db.execute(
            'UPDATE feeding SET timestamp = ?, side = ? WHERE id = ?',
            (timestamp, side, feeding_id)
        )
        db.commit()
    
    @staticmethod
    def delete(feeding_id):
        """Löscht einen Still-Eintrag"""
        db = get_db()
        db.execute('DELETE FROM feeding WHERE id = ?', (feeding_id,))
        db.commit()

class Bottle:
    """Flasche-Tracking"""
    @staticmethod
    def create(timestamp, amount):
        """Erstellt einen Flaschen-Eintrag"""
        db = get_db()
        cursor = db.execute(
            'INSERT INTO bottle (timestamp, amount) VALUES (?, ?)',
            (timestamp, amount)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_latest():
        """Gibt die letzte Flasche zurück"""
        db = get_db()
        row = db.execute(
            'SELECT * FROM bottle ORDER BY timestamp DESC LIMIT 1'
        ).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def get_by_id(bottle_id):
        """Holt einen Flaschen-Eintrag nach ID"""
        db = get_db()
        row = db.execute('SELECT * FROM bottle WHERE id = ?', (bottle_id,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def update(bottle_id, timestamp, amount):
        """Aktualisiert einen Flaschen-Eintrag"""
        db = get_db()
        db.execute(
            'UPDATE bottle SET timestamp = ?, amount = ? WHERE id = ?',
            (timestamp, amount, bottle_id)
        )
        db.commit()
    
    @staticmethod
    def delete(bottle_id):
        """Löscht einen Flaschen-Eintrag"""
        db = get_db()
        db.execute('DELETE FROM bottle WHERE id = ?', (bottle_id,))
        db.commit()

class Diaper:
    """Windel-Tracking"""
    @staticmethod
    def create(timestamp, type):
        """Erstellt einen Windel-Eintrag"""
        db = get_db()
        cursor = db.execute(
            'INSERT INTO diaper (timestamp, type) VALUES (?, ?)',
            (timestamp, type)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_latest():
        """Gibt die letzte Windel zurück"""
        db = get_db()
        row = db.execute(
            'SELECT * FROM diaper ORDER BY timestamp DESC LIMIT 1'
        ).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def get_by_id(diaper_id):
        """Holt einen Windel-Eintrag nach ID"""
        db = get_db()
        row = db.execute('SELECT * FROM diaper WHERE id = ?', (diaper_id,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def update(diaper_id, timestamp, diaper_type):
        """Aktualisiert einen Windel-Eintrag"""
        db = get_db()
        db.execute(
            'UPDATE diaper SET timestamp = ?, type = ? WHERE id = ?',
            (timestamp, diaper_type, diaper_id)
        )
        db.commit()
    
    @staticmethod
    def delete(diaper_id):
        """Löscht einen Windel-Eintrag"""
        db = get_db()
        db.execute('DELETE FROM diaper WHERE id = ?', (diaper_id,))
        db.commit()

class Temperature:
    """Temperatur-Tracking"""
    @staticmethod
    def create(timestamp, value):
        """Erstellt einen Temperatur-Eintrag"""
        db = get_db()
        cursor = db.execute(
            'INSERT INTO temperature (timestamp, value) VALUES (?, ?)',
            (timestamp, value)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(temp_id):
        """Holt einen Temperatur-Eintrag nach ID"""
        db = get_db()
        row = db.execute('SELECT * FROM temperature WHERE id = ?', (temp_id,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def update(temp_id, timestamp, value):
        """Aktualisiert einen Temperatur-Eintrag"""
        db = get_db()
        db.execute(
            'UPDATE temperature SET timestamp = ?, value = ? WHERE id = ?',
            (timestamp, value, temp_id)
        )
        db.commit()
    
    @staticmethod
    def delete(temp_id):
        """Löscht einen Temperatur-Eintrag"""
        db = get_db()
        db.execute('DELETE FROM temperature WHERE id = ?', (temp_id,))
        db.commit()
    
    @staticmethod
    def get_temperature_statistics(start_date, end_date):
        """Gibt Temperatur-Statistiken für einen Zeitraum zurück"""
        db = get_db()
        
        # Alle Temperatur-Einträge im Zeitraum
        rows = db.execute(
            '''SELECT timestamp, value FROM temperature 
               WHERE date(timestamp) >= ? AND date(timestamp) <= ?
               ORDER BY timestamp''',
            (start_date, end_date)
        ).fetchall()
        
        daily_temps = {}  # {date: [temperatures]}
        all_temps = []  # Liste aller Temperatur-Einträge mit vollständigem Zeitstempel
        
        for row in rows:
            try:
                ts = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                day_key = ts.date().isoformat()
                
                if day_key not in daily_temps:
                    daily_temps[day_key] = []
                
                daily_temps[day_key].append(row['value'])
                all_temps.append({
                    'date': day_key,
                    'timestamp': row['timestamp'],
                    'datetime': ts,
                    'value': row['value']
                })
            except (ValueError, AttributeError):
                continue
        
        # Durchschnittswerte pro Tag berechnen (für Übersicht)
        daily_avg = {}
        for day, temps in daily_temps.items():
            if temps:
                daily_avg[day] = round(sum(temps) / len(temps), 1)
        
        # Gesamtdurchschnitt
        if all_temps:
            avg_temp = round(sum(t['value'] for t in all_temps) / len(all_temps), 1)
            min_temp = round(min(t['value'] for t in all_temps), 1)
            max_temp = round(max(t['value'] for t in all_temps), 1)
        else:
            avg_temp = 0
            min_temp = 0
            max_temp = 0
        
        return {
            'daily_avg': daily_avg,  # {date: avg_temp} - für Tagesübersicht
            'all_temps': all_temps,  # Liste aller Temperatur-Einträge mit Zeitstempel
            'avg_temp': avg_temp,
            'min_temp': min_temp,
            'max_temp': max_temp,
            'count': len(all_temps)
        }

class Medicine:
    """Medizin-Tracking"""
    @staticmethod
    def create(timestamp, name, dose):
        """Erstellt einen Medizin-Eintrag"""
        db = get_db()
        cursor = db.execute(
            'INSERT INTO medicine (timestamp, name, dose) VALUES (?, ?, ?)',
            (timestamp, name, dose)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(med_id):
        """Holt einen Medizin-Eintrag nach ID"""
        db = get_db()
        row = db.execute('SELECT * FROM medicine WHERE id = ?', (med_id,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def update(med_id, timestamp, name, dose):
        """Aktualisiert einen Medizin-Eintrag"""
        db = get_db()
        db.execute(
            'UPDATE medicine SET timestamp = ?, name = ?, dose = ? WHERE id = ?',
            (timestamp, name, dose, med_id)
        )
        db.commit()
    
    @staticmethod
    def delete(med_id):
        """Löscht einen Medizin-Eintrag"""
        db = get_db()
        db.execute('DELETE FROM medicine WHERE id = ?', (med_id,))
        db.commit()

def get_all_entries_today(selected_date=None):
    """Gibt alle Einträge eines bestimmten Tages chronologisch zurück"""
    db = get_db()
    if selected_date is None:
        selected_date = date.today()
    elif isinstance(selected_date, str):
        selected_date = date.fromisoformat(selected_date)
    target_date = selected_date.isoformat()
    
    entries = []
    
    # Schlaf: Einträge, die am Tag gestartet haben
    sleep_rows = db.execute(
        'SELECT id, "sleep" as category, type, start_time as timestamp, end_time FROM sleep WHERE date(start_time) = ?',
        (target_date,)
    ).fetchall()
    for row in sleep_rows:
        sleep_type_display = "Nachtschlaf" if row['type'] == 'night' else "Nickerchen"
        entries.append({
            'id': row['id'],
            'category': 'sleep',
            'type': row['type'],
            'timestamp': row['timestamp'],
            'end_time': row['end_time'],
            'display': sleep_type_display
        })
    
    # Schlaf: Einträge, die am vorherigen Tag gestartet haben, aber am Tag enden
    prev_date = (selected_date - timedelta(days=1)).isoformat()
    sleep_rows_prev = db.execute(
        '''SELECT id, "sleep" as category, type, start_time as timestamp, end_time 
           FROM sleep 
           WHERE date(start_time) = ? AND date(end_time) = ? AND end_time IS NOT NULL''',
        (prev_date, target_date)
    ).fetchall()
    for row in sleep_rows_prev:
        sleep_type_display = "Nachtschlaf" if row['type'] == 'night' else "Nickerchen"
        entries.append({
            'id': row['id'],
            'category': 'sleep',
            'type': row['type'],
            'timestamp': row['timestamp'],
            'end_time': row['end_time'],
            'display': sleep_type_display
        })
    
    # Stillen
    feeding_rows = db.execute(
        'SELECT id, "feeding" as category, timestamp, side FROM feeding WHERE date(timestamp) = ?',
        (target_date,)
    ).fetchall()
    for row in feeding_rows:
        entries.append({
            'id': row['id'],
            'category': 'feeding',
            'timestamp': row['timestamp'],
            'side': row['side'],
            'display': f"Stillen ({row['side']})"
        })
    
    # Flasche
    bottle_rows = db.execute(
        'SELECT id, "bottle" as category, timestamp, amount FROM bottle WHERE date(timestamp) = ?',
        (target_date,)
    ).fetchall()
    for row in bottle_rows:
        entries.append({
            'id': row['id'],
            'category': 'bottle',
            'timestamp': row['timestamp'],
            'amount': row['amount'],
            'display': f"Flasche ({row['amount']} ml)"
        })
    
    # Windel
    diaper_rows = db.execute(
        'SELECT id, "diaper" as category, timestamp, type FROM diaper WHERE date(timestamp) = ?',
        (target_date,)
    ).fetchall()
    for row in diaper_rows:
        entries.append({
            'id': row['id'],
            'category': 'diaper',
            'timestamp': row['timestamp'],
            'type': row['type'],
            'display': f"Windel ({row['type']})"
        })
    
    # Temperatur
    temp_rows = db.execute(
        'SELECT id, "temperature" as category, timestamp, value FROM temperature WHERE date(timestamp) = ?',
        (target_date,)
    ).fetchall()
    for row in temp_rows:
        entries.append({
            'id': row['id'],
            'category': 'temperature',
            'timestamp': row['timestamp'],
            'value': row['value'],
            'display': f"Temperatur ({row['value']}°C)"
        })
    
    # Medizin
    med_rows = db.execute(
        'SELECT id, "medicine" as category, timestamp, name, dose FROM medicine WHERE date(timestamp) = ?',
        (target_date,)
    ).fetchall()
    for row in med_rows:
        entries.append({
            'id': row['id'],
            'category': 'medicine',
            'timestamp': row['timestamp'],
            'name': row['name'],
            'dose': row['dose'],
            'display': f"Medizin ({row['name']}, {row['dose']})"
        })
    
    # Sortiere nach Zeitstempel
    entries.sort(key=lambda x: x['timestamp'], reverse=True)
    return entries

def get_latest_activities(limit=3):
    """Gibt die letzten N Aktivitäten zurück (unabhängig von der Kategorie)"""
    db = get_db()
    
    all_entries = []
    
    # Schlaf
    sleep_rows = db.execute(
        'SELECT id, "sleep" as category, type, start_time as timestamp, end_time FROM sleep ORDER BY start_time DESC LIMIT ?',
        (limit * 2,)  # Mehr holen, da wir später filtern
    ).fetchall()
    for row in sleep_rows:
        all_entries.append({
            'category': 'sleep',
            'type': row['type'],
            'timestamp': row['timestamp'],
            'end_time': row['end_time'],
            'display': f"Schlaf ({row['type']})"
        })
    
    # Stillen
    feeding_rows = db.execute(
        'SELECT id, "feeding" as category, timestamp, side FROM feeding ORDER BY timestamp DESC LIMIT ?',
        (limit * 2,)
    ).fetchall()
    for row in feeding_rows:
        all_entries.append({
            'category': 'feeding',
            'timestamp': row['timestamp'],
            'side': row['side'],
            'display': f"Stillen ({row['side']})"
        })
    
    # Flasche
    bottle_rows = db.execute(
        'SELECT id, "bottle" as category, timestamp, amount FROM bottle ORDER BY timestamp DESC LIMIT ?',
        (limit * 2,)
    ).fetchall()
    for row in bottle_rows:
        all_entries.append({
            'category': 'bottle',
            'timestamp': row['timestamp'],
            'amount': row['amount'],
            'display': f"Flasche ({row['amount']} ml)"
        })
    
    # Windel
    diaper_rows = db.execute(
        'SELECT id, "diaper" as category, timestamp, type FROM diaper ORDER BY timestamp DESC LIMIT ?',
        (limit * 2,)
    ).fetchall()
    for row in diaper_rows:
        all_entries.append({
            'category': 'diaper',
            'timestamp': row['timestamp'],
            'type': row['type'],
            'display': f"Windel ({row['type']})"
        })
    
    # Temperatur
    temp_rows = db.execute(
        'SELECT id, "temperature" as category, timestamp, value FROM temperature ORDER BY timestamp DESC LIMIT ?',
        (limit * 2,)
    ).fetchall()
    for row in temp_rows:
        all_entries.append({
            'category': 'temperature',
            'timestamp': row['timestamp'],
            'value': row['value'],
            'display': f"Temperatur ({row['value']}°C)"
        })
    
    # Medizin
    med_rows = db.execute(
        'SELECT id, "medicine" as category, timestamp, name, dose FROM medicine ORDER BY timestamp DESC LIMIT ?',
        (limit * 2,)
    ).fetchall()
    for row in med_rows:
        all_entries.append({
            'category': 'medicine',
            'timestamp': row['timestamp'],
            'name': row['name'],
            'dose': row['dose'],
            'display': f"Medizin ({row['name']}, {row['dose']})"
        })
    
    # Sortiere nach Zeitstempel und nimm die letzten N
    all_entries.sort(key=lambda x: x['timestamp'], reverse=True)
    return all_entries[:limit]

class BabyInfo:
    """Baby-Informationen für Nickerchen-Vorschläge"""
    
    @staticmethod
    def get_birth_date():
        """Holt das Geburtsdatum des Babys"""
        db = get_db()
        row = db.execute('SELECT birth_date FROM baby_info ORDER BY id LIMIT 1').fetchone()
        if row:
            return date.fromisoformat(row['birth_date'])
        return None
    
    @staticmethod
    def set_birth_date(birth_date):
        """Setzt das Geburtsdatum des Babys"""
        db = get_db()
        # Prüfe ob bereits ein Eintrag existiert
        existing = db.execute('SELECT id FROM baby_info ORDER BY id LIMIT 1').fetchone()
        if existing:
            db.execute(
                'UPDATE baby_info SET birth_date = ?, updated_at = ? WHERE id = ?',
                (birth_date.isoformat(), datetime.now(tz_berlin).isoformat(), existing['id'])
            )
        else:
            db.execute(
                'INSERT INTO baby_info (birth_date) VALUES (?)',
                (birth_date.isoformat(),)
            )
        db.commit()
    
    @staticmethod
    def get_age_months():
        """Berechnet das Alter des Babys in Monaten"""
        birth_date = BabyInfo.get_birth_date()
        if not birth_date:
            return 6  # Standard: 6 Monate
        today = date.today()
        months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
        if today.day < birth_date.day:
            months -= 1
        return max(0, months)
    
    @staticmethod
    def get_sleep_recommendations():
        """Gibt die empfohlenen Schlafzeiten basierend auf dem Alter zurück"""
        age_months = BabyInfo.get_age_months()
        
        # Empfohlene Gesamtschlafdauer und Tagschlaf basierend auf Alter
        recommendations = {
            0: {'total': 16, 'night': 8.5, 'day': 8, 'naps': (3, 5)},
            1: {'total': 15.5, 'night': 8.5, 'day': 7, 'naps': (3, 5)},
            3: {'total': 15, 'night': 9.5, 'day': 4.5, 'naps': (2, 4)},
            4: {'total': 15, 'night': 9.5, 'day': 4.5, 'naps': (3, 5)},
            5: {'total': 15, 'night': 9.5, 'day': 4.5, 'naps': (2, 5)},
            6: {'total': 14, 'night': 10, 'day': 4, 'naps': (2, 4)},
            7: {'total': 14, 'night': 10, 'day': 4, 'naps': (2, 4)},
            8: {'total': 14, 'night': 11, 'day': 3, 'naps': (1, 3)},
            9: {'total': 14, 'night': 11, 'day': 3, 'naps': (1, 3)},
            10: {'total': 14, 'night': 11, 'day': 3, 'naps': (1, 3)},
            11: {'total': 14, 'night': 11, 'day': 3, 'naps': (1, 3)},
            12: {'total': 14, 'night': 11, 'day': 3, 'naps': (1, 2)},
            16: {'total': 13.5, 'night': 11, 'day': 2.5, 'naps': (1, 1)},
            18: {'total': 13.5, 'night': 11, 'day': 2.5, 'naps': (1, 1)},
            24: {'total': 13, 'night': 11, 'day': 2, 'naps': (1, 1)},
        }
        
        # Finde die passende Empfehlung (nächstkleineres Alter)
        age_keys = sorted([k for k in recommendations.keys() if k <= age_months], reverse=True)
        if age_keys:
            return recommendations[age_keys[0]]
        # Fallback für ältere Kinder
        return {'total': 12, 'night': 11, 'day': 1, 'naps': (0, 1)}
    
    @staticmethod
    def get_nap_suggestions(selected_date=None):
        """Berechnet Vorschläge für das nächste Nickerchen"""
        if selected_date is None:
            selected_date = date.today()
        
        recommendations = BabyInfo.get_sleep_recommendations()
        min_naps, max_naps = recommendations['naps']
        # Berechne empfohlene Anzahl (Mittelwert, gerundet)
        target_naps = round((min_naps + max_naps) / 2)
        target_day_sleep = recommendations['day']
        
        # Hole alle Nickerchen des Tages
        db = get_db()
        naps_today = db.execute(
            '''SELECT start_time, end_time FROM sleep 
               WHERE type = 'nap' 
               AND (date(start_time) = ? OR (date(start_time) = ? AND date(end_time) = ?))
               AND end_time IS NOT NULL''',
            (selected_date.isoformat(), (selected_date - timedelta(days=1)).isoformat(), selected_date.isoformat())
        ).fetchall()
        
        completed_naps = len(naps_today)
        
        # Berechne bereits geschlafene Tagschlafdauer
        total_day_sleep_hours = 0.0
        for nap in naps_today:
            try:
                start_dt = datetime.fromisoformat(nap['start_time'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(nap['end_time'].replace('Z', '+00:00'))
                if start_dt.tzinfo is None:
                    start_dt = tz_berlin.localize(start_dt.replace(tzinfo=None))
                if end_dt.tzinfo is None:
                    end_dt = tz_berlin.localize(end_dt.replace(tzinfo=None))
                duration = (end_dt - start_dt).total_seconds() / 3600.0
                total_day_sleep_hours += duration
            except (ValueError, AttributeError):
                continue
        
        # Prüfe ob noch ein Nickerchen empfohlen wird
        suggestions = []
        
        if completed_naps < target_naps:
            # Berechne verbleibende Tagschlafdauer
            remaining_day_sleep = target_day_sleep - total_day_sleep_hours
            
            if remaining_day_sleep > 0.5:  # Mindestens 30 Minuten
                # Berechne nächste empfohlene Zeit basierend auf letztem Aufwachen
                now = datetime.now(tz_berlin)
                last_wake_time = None
                
                # Finde letztes Aufwachen (Ende eines Nickerchens oder Nachtschlafs)
                last_sleep_end = db.execute(
                    '''SELECT end_time FROM sleep 
                       WHERE end_time IS NOT NULL 
                       AND date(end_time) = ?
                       ORDER BY end_time DESC LIMIT 1''',
                    (selected_date.isoformat(),)
                ).fetchone()
                
                if last_sleep_end:
                    try:
                        last_wake_time = datetime.fromisoformat(last_sleep_end['end_time'].replace('Z', '+00:00'))
                        if last_wake_time.tzinfo is None:
                            last_wake_time = tz_berlin.localize(last_wake_time.replace(tzinfo=None))
                    except (ValueError, AttributeError):
                        pass
                
                # Wenn kein Aufwachen heute, nimm aktuelles Datum/Zeit
                if not last_wake_time or last_wake_time.date() != selected_date:
                    last_wake_time = now
                
                # Empfohlene Wachzeit vor nächstem Nickerchen
                # Berücksichtigt: Alter, Tageszeit und Anzahl der bereits gemachten Nickerchen
                age_months = BabyInfo.get_age_months()
                current_hour = last_wake_time.hour
                
                # Basis-Wachzeit basierend auf Alter
                if age_months <= 3:
                    base_wake_window = 1.0  # 1 Stunde
                elif age_months <= 4:
                    base_wake_window = 1.5  # 1.5 Stunden
                elif age_months <= 6:
                    base_wake_window = 2.0  # 2 Stunden
                elif age_months <= 9:
                    base_wake_window = 2.5  # 2.5 Stunden
                elif age_months <= 12:
                    base_wake_window = 3.0  # 3 Stunden
                else:
                    base_wake_window = 3.5  # 3.5 Stunden
                
                # Anpassung basierend auf Tageszeit
                # Morgens (6-10 Uhr): kürzere Wachzeit
                # Mittags (10-14 Uhr): mittlere Wachzeit
                # Nachmittags (14-18 Uhr): längere Wachzeit
                if current_hour < 10:
                    time_adjustment = -0.25  # 15 Minuten kürzer morgens
                elif current_hour < 14:
                    time_adjustment = 0.0  # Keine Anpassung mittags
                else:
                    time_adjustment = 0.5  # 30 Minuten länger nachmittags
                
                # Anpassung basierend auf Anzahl der bereits gemachten Nickerchen
                # Je mehr Nickerchen bereits gemacht wurden, desto länger die Wachzeit
                nap_adjustment = completed_naps * 0.25  # +15 Minuten pro bereits gemachtem Nickerchen
                
                # Berechne finale Wachzeit
                wake_window = base_wake_window + time_adjustment + nap_adjustment
                
                # Stelle sicher, dass die Wachzeit nicht zu kurz wird (Minimum 1 Stunde)
                wake_window = max(1.0, wake_window)
                
                # Berechne nächste empfohlene Nickerchen-Zeit
                suggested_time = last_wake_time + timedelta(hours=wake_window)
                
                # Stelle sicher, dass die Zeit nicht in der Vergangenheit liegt
                if suggested_time < now:
                    suggested_time = now + timedelta(minutes=15)  # Mindestens 15 Minuten ab jetzt
                
                # Empfohlene Dauer des Nickerchens
                if age_months <= 3:
                    nap_duration = 1.5  # 1.5 Stunden
                elif age_months <= 6:
                    nap_duration = 1.5  # 1.5 Stunden
                elif age_months <= 12:
                    nap_duration = 1.0  # 1 Stunde
                else:
                    nap_duration = 1.0  # 1 Stunde
                
                suggestions.append({
                    'suggested_time': suggested_time,
                    'nap_duration': nap_duration,
                    'remaining_day_sleep': remaining_day_sleep,
                    'completed_naps': completed_naps,
                    'target_naps': target_naps,
                    'min_naps': min_naps,
                    'max_naps': max_naps
                })
        
        return suggestions

