"""Datenmodelle für die Baby-Tracking App"""
from app.models.database import get_db
from datetime import datetime, date, timedelta

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
        if selected_date is None:
            selected_date = date.today()
        elif isinstance(selected_date, str):
            selected_date = date.fromisoformat(selected_date)
        target_date = selected_date.isoformat()
        
        # Schlaf-Einträge, die am Tag gestartet haben
        rows = db.execute(
            '''SELECT start_time, end_time FROM sleep 
               WHERE date(start_time) = ? AND end_time IS NOT NULL''',
            (target_date,)
        ).fetchall()
        
        # Schlaf-Einträge, die am vorherigen Tag gestartet haben, aber am Tag enden
        prev_date = (selected_date - timedelta(days=1)).isoformat()
        rows_prev = db.execute(
            '''SELECT start_time, end_time FROM sleep 
               WHERE date(start_time) = ? AND date(end_time) = ? AND end_time IS NOT NULL''',
            (prev_date, target_date)
        ).fetchall()
        
        total_seconds = 0
        
        # Einträge, die am Tag gestartet haben
        for row in rows:
            try:
                start = datetime.fromisoformat(row['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(row['end_time'].replace('Z', '+00:00'))
                total_seconds += (end - start).total_seconds()
            except (ValueError, AttributeError):
                continue
        
        # Einträge, die am vorherigen Tag gestartet haben, aber am Tag enden
        # Nur der Teil, der am Tag liegt
        for row in rows_prev:
            try:
                start = datetime.fromisoformat(row['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(row['end_time'].replace('Z', '+00:00'))
                # Nur der Teil vom Tagbeginn bis zum Ende zählen
                day_start = datetime.combine(selected_date, datetime.min.time())
                if end > day_start:
                    sleep_duration = (end - day_start).total_seconds()
                    total_seconds += sleep_duration
            except (ValueError, AttributeError):
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
                
                # Wenn der Schlaf über Mitternacht geht, aufteilen
                if start.date() != end.date():
                    # Teil 1: Vom Start bis Mitternacht
                    day1_key = start.date().isoformat()
                    if start_date <= day1_key <= end_date:
                        midnight_day1 = datetime.combine(start.date(), datetime.max.time().replace(hour=23, minute=59, second=59))
                        duration_day1 = (midnight_day1 - start).total_seconds() / 3600
                        if day1_key not in daily_sleep:
                            daily_sleep[day1_key] = 0
                        daily_sleep[day1_key] += duration_day1
                    
                    # Teil 2: Von Mitternacht bis Ende
                    day2_key = end.date().isoformat()
                    if start_date <= day2_key <= end_date:
                        midnight_day2 = datetime.combine(end.date(), datetime.min.time())
                        duration_day2 = (end - midnight_day2).total_seconds() / 3600
                        if day2_key not in daily_sleep:
                            daily_sleep[day2_key] = 0
                        daily_sleep[day2_key] += duration_day2
                    
                    # Gesamtdauer für Typ-Berechnung
                    duration_hours = (end - start).total_seconds() / 3600
                else:
                    # Schlaf innerhalb eines Tages
                    day_key = start.date().isoformat()
                    if start_date <= day_key <= end_date:
                        duration_hours = (end - start).total_seconds() / 3600
                        if day_key not in daily_sleep:
                            daily_sleep[day_key] = 0
                        daily_sleep[day_key] += duration_hours
                    else:
                        duration_hours = 0
                
                if row['type'] == 'nap':
                    nap_hours += duration_hours
                else:
                    night_hours += duration_hours
                
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
                
                # Nur der Teil vom Zeitraumbeginn bis zum Ende zählt
                start_of_period = datetime.combine(date.fromisoformat(start_date), datetime.min.time())
                if start < start_of_period:
                    # Nur der Teil im Zeitraum zählen
                    duration_hours = (end - start_of_period).total_seconds() / 3600
                    
                    # Auf die Tage im Zeitraum aufteilen
                    current_date = start_of_period.date()
                    remaining_duration = duration_hours
                    
                    while current_date <= end.date() and current_date <= date.fromisoformat(end_date):
                        day_key = current_date.isoformat()
                        if current_date == end.date():
                            # Letzter Tag: von Tagesbeginn bis Endzeit
                            day_start = datetime.combine(current_date, datetime.min.time())
                            day_duration = (end - day_start).total_seconds() / 3600
                        else:
                            # Vollständiger Tag
                            day_duration = 24.0
                        
                        if day_key not in daily_sleep:
                            daily_sleep[day_key] = 0
                        daily_sleep[day_key] += day_duration
                        remaining_duration -= day_duration
                        current_date += timedelta(days=1)
                else:
                    duration_hours = (end - start).total_seconds() / 3600
                
                if row['type'] == 'nap':
                    nap_hours += duration_hours
                else:
                    night_hours += duration_hours
                
                # Aufwachzeit (end_time)
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

