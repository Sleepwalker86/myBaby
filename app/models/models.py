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
        
        # PERFORMANCE-OPTIMIERUNG: Hole nur relevante Schlaf-Einträge mit Range-Query
        # Statt alle Einträge zu holen, filtern wir direkt in der DB
        # Ein Tag: von 00:00:00 bis 23:59:59
        day_start = datetime.combine(selected_date, datetime.min.time())
        day_end = datetime.combine(selected_date, datetime.max.time().replace(hour=23, minute=59, second=59))
        day_start_str = day_start.strftime('%Y-%m-%dT%H:%M:%S')
        day_end_str = day_end.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Hole nur Einträge, die am ausgewählten Tag enden
        # Dies nutzt den Index auf end_time viel besser als date(end_time)
        all_rows = db.execute(
            '''SELECT type, start_time, end_time FROM sleep 
               WHERE end_time IS NOT NULL 
               AND end_time >= ? AND end_time <= ?''',
            (day_start_str, day_end_str)
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
                    
                    # Für Nachtschlaf: Ziehe nächtliches Aufwachen ab
                    if sleep_type == 'night':
                        waking_duration = NightWaking.get_total_waking_duration(
                            start_str, end_str
                        )
                        duration_seconds = max(0, duration_seconds - (waking_duration * 3600))
                    
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
                                
                                # Ziehe nächtliches Aufwachen ab (für aktiven Nachtschlaf)
                                # Verwende die aktuelle Zeit als Endzeit für die Berechnung
                                now_str = datetime.now(tz_berlin).isoformat()
                                waking_duration = NightWaking.get_total_waking_duration(
                                    row['start_time'], now_str
                                )
                                duration_seconds = max(0, duration_seconds - (waking_duration * 3600))
                                
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
        
        # PERFORMANCE-OPTIMIERUNG: Range-Queries statt date() für bessere Index-Nutzung
        # Konvertiere Datums-Strings zu datetime für Range-Queries
        if isinstance(start_date, str):
            start_date_obj = date.fromisoformat(start_date)
        else:
            start_date_obj = start_date
        if isinstance(end_date, str):
            end_date_obj = date.fromisoformat(end_date)
        else:
            end_date_obj = end_date
        
        range_start = datetime.combine(start_date_obj, datetime.min.time())
        range_end = datetime.combine(end_date_obj, datetime.max.time().replace(hour=23, minute=59, second=59))
        range_start_str = range_start.strftime('%Y-%m-%dT%H:%M:%S')
        range_end_str = range_end.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Alle Schlaf-Einträge, die im Zeitraum gestartet haben
        rows = db.execute(
            '''SELECT type, start_time, end_time FROM sleep 
               WHERE start_time >= ? AND start_time <= ? AND end_time IS NOT NULL
               ORDER BY start_time''',
            (range_start_str, range_end_str)
        ).fetchall()
        
        # Schlaf-Einträge, die vor dem Zeitraum gestartet haben, aber im Zeitraum enden
        rows_prev = db.execute(
            '''SELECT type, start_time, end_time FROM sleep 
               WHERE start_time < ? AND end_time >= ? AND end_time <= ? AND end_time IS NOT NULL
               ORDER BY start_time''',
            (range_start_str, range_start_str, range_end_str)
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
                    # Ziehe nächtliches Aufwachen ab
                    waking_duration = NightWaking.get_total_waking_duration(
                        row['start_time'], row['end_time']
                    )
                    duration_hours = max(0, duration_hours - waking_duration)
                    
                    day_key = end.date().isoformat()
                    # PERFORMANCE: Direkter Vergleich statt String-Konvertierung
                    if start_date_obj <= end.date() <= end_date_obj:
                        if day_key not in daily_sleep:
                            daily_sleep[day_key] = 0
                        daily_sleep[day_key] += duration_hours
                else:
                    # Nickerchen: Wenn über Mitternacht, aufteilen (oder auch dem End-Tag zurechnen?)
                    # Für Konsistenz: Auch Nickerchen dem End-Tag zurechnen
                    if start.date() != end.date():
                        # Über Mitternacht: Dem End-Tag zurechnen
                        day_key = end.date().isoformat()
                        # PERFORMANCE: Direkter Vergleich statt String-Konvertierung
                        if start_date_obj <= end.date() <= end_date_obj:
                            if day_key not in daily_sleep:
                                daily_sleep[day_key] = 0
                            daily_sleep[day_key] += duration_hours
                    else:
                        # Innerhalb eines Tages
                        day_key = start.date().isoformat()
                        # PERFORMANCE: Direkter Vergleich statt String-Konvertierung
                        if start_date_obj <= start.date() <= end_date_obj:
                            if day_key not in daily_sleep:
                                daily_sleep[day_key] = 0
                            daily_sleep[day_key] += duration_hours
                
                if row['type'] == 'nap':
                    nap_hours += duration_hours
                else:
                    night_hours += duration_hours
                    # Aufwachzeit und Einschlafzeit: Nur für Nachtschlaf
                    # PERFORMANCE: Direkter Vergleich statt String-Konvertierung
                    # Aufwachzeit (end_time) - nur wenn im Zeitraum
                    if start_date_obj <= end.date() <= end_date_obj:
                        wake_times.append(end.hour + end.minute / 60.0)
                    # Einschlafzeit (start_time) - nur wenn im Zeitraum
                    if start_date_obj <= start.date() <= end_date_obj:
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
                    # Ziehe nächtliches Aufwachen ab
                    waking_duration = NightWaking.get_total_waking_duration(
                        row['start_time'], row['end_time']
                    )
                    duration_hours = max(0, duration_hours - waking_duration)
                    
                    day_key = end.date().isoformat()
                    # PERFORMANCE: Direkter Vergleich statt String-Konvertierung
                    if start_date_obj <= end.date() <= end_date_obj:
                        if day_key not in daily_sleep:
                            daily_sleep[day_key] = 0
                        daily_sleep[day_key] += duration_hours
                else:
                    # Nickerchen: Nur der Teil im Zeitraum
                    start_of_period = tz_berlin.localize(datetime.combine(start_date_obj, datetime.min.time()))
                    if start < start_of_period:
                        # Nur der Teil im Zeitraum zählen
                        day_key = end.date().isoformat()
                        # PERFORMANCE: Direkter Vergleich statt String-Konvertierung
                        if start_date_obj <= end.date() <= end_date_obj:
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

class NightWaking:
    """Nächtliches Aufwachen-Tracking"""
    @staticmethod
    def create(start_time, end_time=None):
        """Erstellt einen nächtliches Aufwachen-Eintrag"""
        db = get_db()
        cursor = db.execute(
            'INSERT INTO night_waking (start_time, end_time) VALUES (?, ?)',
            (start_time, end_time)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_active():
        """Gibt das aktive nächtliche Aufwachen zurück (falls vorhanden)"""
        db = get_db()
        row = db.execute(
            'SELECT * FROM night_waking WHERE end_time IS NULL ORDER BY start_time DESC LIMIT 1'
        ).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def end_waking(waking_id, end_time):
        """Beendet ein nächtliches Aufwachen"""
        db = get_db()
        db.execute(
            'UPDATE night_waking SET end_time = ? WHERE id = ?',
            (end_time, waking_id)
        )
        db.commit()
    
    @staticmethod
    def get_by_id(waking_id):
        """Holt einen nächtliches Aufwachen-Eintrag nach ID"""
        db = get_db()
        row = db.execute('SELECT * FROM night_waking WHERE id = ?', (waking_id,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def get_wakings_for_night_sleep(night_sleep_start, night_sleep_end):
        """Gibt alle nächtlichen Aufwachen für einen bestimmten Nachtschlaf zurück"""
        db = get_db()
        rows = db.execute(
            '''SELECT * FROM night_waking 
               WHERE start_time >= ? AND start_time <= ?
               AND (end_time IS NULL OR (end_time >= ? AND end_time <= ?))
               ORDER BY start_time''',
            (night_sleep_start, night_sleep_end, night_sleep_start, night_sleep_end)
        ).fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_total_waking_duration(night_sleep_start, night_sleep_end):
        """Berechnet die Gesamtdauer des nächtlichen Aufwachens für einen Nachtschlaf in Stunden"""
        wakings = NightWaking.get_wakings_for_night_sleep(night_sleep_start, night_sleep_end)
        total_seconds = 0.0
        
        for waking in wakings:
            if not waking.get('end_time'):
                # Aktives Aufwachen: bis zum aktuellen Zeitpunkt oder Nachtschlaf-Ende
                now = datetime.now(tz_berlin)
                try:
                    end_dt = datetime.fromisoformat(night_sleep_end.replace('Z', '+00:00'))
                    if end_dt.tzinfo is None:
                        end_dt = tz_berlin.localize(end_dt.replace(tzinfo=None))
                    elif end_dt.tzinfo != tz_berlin:
                        end_dt = end_dt.astimezone(tz_berlin)
                    end_time = min(now, end_dt)
                except (ValueError, AttributeError):
                    end_time = now
            else:
                try:
                    end_time = datetime.fromisoformat(waking['end_time'].replace('Z', '+00:00'))
                    if end_time.tzinfo is None:
                        end_time = tz_berlin.localize(end_time.replace(tzinfo=None))
                    elif end_time.tzinfo != tz_berlin:
                        end_time = end_time.astimezone(tz_berlin)
                except (ValueError, AttributeError):
                    continue
            
            try:
                start_time = datetime.fromisoformat(waking['start_time'].replace('Z', '+00:00'))
                if start_time.tzinfo is None:
                    start_time = tz_berlin.localize(start_time.replace(tzinfo=None))
                elif start_time.tzinfo != tz_berlin:
                    start_time = start_time.astimezone(tz_berlin)
                
                # Prüfe ob das Aufwachen innerhalb des Nachtschlafs liegt
                try:
                    sleep_start = datetime.fromisoformat(night_sleep_start.replace('Z', '+00:00'))
                    if sleep_start.tzinfo is None:
                        sleep_start = tz_berlin.localize(sleep_start.replace(tzinfo=None))
                    elif sleep_start.tzinfo != tz_berlin:
                        sleep_start = sleep_start.astimezone(tz_berlin)
                    
                    sleep_end = datetime.fromisoformat(night_sleep_end.replace('Z', '+00:00'))
                    if sleep_end.tzinfo is None:
                        sleep_end = tz_berlin.localize(sleep_end.replace(tzinfo=None))
                    elif sleep_end.tzinfo != tz_berlin:
                        sleep_end = sleep_end.astimezone(tz_berlin)
                    
                    # Nur Aufwachen innerhalb des Nachtschlafs zählen
                    if start_time >= sleep_start and end_time <= sleep_end:
                        duration_seconds = (end_time - start_time).total_seconds()
                        total_seconds += duration_seconds
                except (ValueError, AttributeError):
                    pass
            except (ValueError, AttributeError):
                continue
        
        return round(total_seconds / 3600, 2) if total_seconds > 0 else 0.0
    
    @staticmethod
    def update(waking_id, start_time, end_time=None):
        """Aktualisiert einen nächtliches Aufwachen-Eintrag"""
        db = get_db()
        db.execute(
            'UPDATE night_waking SET start_time = ?, end_time = ? WHERE id = ?',
            (start_time, end_time, waking_id)
        )
        db.commit()
    
    @staticmethod
    def delete(waking_id):
        """Löscht einen nächtliches Aufwachen-Eintrag"""
        db = get_db()
        db.execute('DELETE FROM night_waking WHERE id = ?', (waking_id,))
        db.commit()

class Feeding:
    """Stillen-Tracking"""
    @staticmethod
    def create(timestamp, side, end_time=None):
        """Erstellt einen Still-Eintrag"""
        db = get_db()
        cursor = db.execute(
            'INSERT INTO feeding (timestamp, side, end_time) VALUES (?, ?, ?)',
            (timestamp, side, end_time)
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
    def update(feeding_id, timestamp, side, end_time=None):
        """Aktualisiert einen Still-Eintrag"""
        db = get_db()
        db.execute(
            'UPDATE feeding SET timestamp = ?, side = ?, end_time = ? WHERE id = ?',
            (timestamp, side, end_time, feeding_id)
        )
        db.commit()
    
    @staticmethod
    def delete(feeding_id):
        """Löscht einen Still-Eintrag"""
        db = get_db()
        db.execute('DELETE FROM feeding WHERE id = ?', (feeding_id,))
        db.commit()
    
    @staticmethod
    def get_feeding_statistics(start_date, end_date):
        """Gibt Still-Statistiken für einen Zeitraum zurück"""
        db = get_db()
        
        # PERFORMANCE: Range-Query statt date() für bessere Index-Nutzung
        if isinstance(start_date, str):
            start_date_obj = date.fromisoformat(start_date)
        else:
            start_date_obj = start_date
        if isinstance(end_date, str):
            end_date_obj = date.fromisoformat(end_date)
        else:
            end_date_obj = end_date
        
        range_start = datetime.combine(start_date_obj, datetime.min.time())
        range_end = datetime.combine(end_date_obj, datetime.max.time().replace(hour=23, minute=59, second=59))
        range_start_str = range_start.strftime('%Y-%m-%dT%H:%M:%S')
        range_end_str = range_end.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Alle Still-Einträge im Zeitraum
        rows = db.execute(
            '''SELECT id FROM feeding 
               WHERE timestamp >= ? AND timestamp <= ?''',
            (range_start_str, range_end_str)
        ).fetchall()
        
        total_count = len(rows)
        
        # Berechne Anzahl der Tage im Zeitraum
        days_count = (end_date_obj - start_date_obj).days + 1
        
        # Durchschnittswert
        avg_count = round(total_count / days_count, 1) if days_count > 0 else 0
        
        return {
            'total_count': total_count,
            'avg_count': avg_count,
            'days_count': days_count
        }

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
    
    @staticmethod
    def get_diaper_statistics(start_date, end_date):
        """Gibt Windel-Statistiken für einen Zeitraum zurück"""
        db = get_db()
        
        # PERFORMANCE: Range-Query statt date() für bessere Index-Nutzung
        if isinstance(start_date, str):
            start_date_obj = date.fromisoformat(start_date)
        else:
            start_date_obj = start_date
        if isinstance(end_date, str):
            end_date_obj = date.fromisoformat(end_date)
        else:
            end_date_obj = end_date
        
        range_start = datetime.combine(start_date_obj, datetime.min.time())
        range_end = datetime.combine(end_date_obj, datetime.max.time().replace(hour=23, minute=59, second=59))
        range_start_str = range_start.strftime('%Y-%m-%dT%H:%M:%S')
        range_end_str = range_end.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Alle Windel-Einträge im Zeitraum
        rows = db.execute(
            '''SELECT type FROM diaper 
               WHERE timestamp >= ? AND timestamp <= ?''',
            (range_start_str, range_end_str)
        ).fetchall()
        
        total_count = len(rows)
        nass_count = 0
        groß_count = 0
        beides_count = 0
        
        for row in rows:
            diaper_type = row['type']
            if diaper_type == 'nass':
                nass_count += 1
            elif diaper_type == 'groß':
                groß_count += 1
            elif diaper_type == 'beides':
                beides_count += 1
        
        # Berechne Anzahl der Tage im Zeitraum
        days_count = (end_date_obj - start_date_obj).days + 1
        
        # Durchschnittswerte
        avg_total = round(total_count / days_count, 1) if days_count > 0 else 0
        avg_nass = round(nass_count / days_count, 1) if days_count > 0 else 0
        avg_groß = round(groß_count / days_count, 1) if days_count > 0 else 0
        
        return {
            'total_count': total_count,
            'nass_count': nass_count,
            'groß_count': groß_count,
            'beides_count': beides_count,
            'avg_total': avg_total,
            'avg_nass': avg_nass,
            'avg_groß': avg_groß,
            'days_count': days_count
        }

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
        # PERFORMANCE: Range-Query statt date() für bessere Index-Nutzung
        if isinstance(start_date, str):
            start_date_obj = date.fromisoformat(start_date)
        else:
            start_date_obj = start_date
        if isinstance(end_date, str):
            end_date_obj = date.fromisoformat(end_date)
        else:
            end_date_obj = end_date
        
        range_start = datetime.combine(start_date_obj, datetime.min.time())
        range_end = datetime.combine(end_date_obj, datetime.max.time().replace(hour=23, minute=59, second=59))
        range_start_str = range_start.strftime('%Y-%m-%dT%H:%M:%S')
        range_end_str = range_end.strftime('%Y-%m-%dT%H:%M:%S')
        
        rows = db.execute(
            '''SELECT timestamp, value FROM temperature 
               WHERE timestamp >= ? AND timestamp <= ?
               ORDER BY timestamp''',
            (range_start_str, range_end_str)
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
    
    # PERFORMANCE-OPTIMIERUNG: Verwende Range-Queries statt date() für bessere Index-Nutzung
    day_start = datetime.combine(selected_date, datetime.min.time())
    day_end = datetime.combine(selected_date, datetime.max.time().replace(hour=23, minute=59, second=59))
    day_start_str = day_start.strftime('%Y-%m-%dT%H:%M:%S')
    day_end_str = day_end.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Für Einträge vom Vortag, die am Tag enden
    prev_date = selected_date - timedelta(days=1)
    prev_day_start = datetime.combine(prev_date, datetime.min.time())
    prev_day_end = datetime.combine(prev_date, datetime.max.time().replace(hour=23, minute=59, second=59))
    prev_day_start_str = prev_day_start.strftime('%Y-%m-%dT%H:%M:%S')
    prev_day_end_str = prev_day_end.strftime('%Y-%m-%dT%H:%M:%S')
    
    entries = []
    
    # Schlaf: Einträge, die am Tag gestartet haben (nutzt Index auf start_time)
    sleep_rows = db.execute(
        '''SELECT id, "sleep" as category, type, start_time as timestamp, end_time 
           FROM sleep 
           WHERE start_time >= ? AND start_time <= ?''',
        (day_start_str, day_end_str)
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
    # PERFORMANCE: Range-Query nutzt Indizes besser als date()
    sleep_rows_prev = db.execute(
        '''SELECT id, "sleep" as category, type, start_time as timestamp, end_time 
           FROM sleep 
           WHERE start_time >= ? AND start_time <= ? 
           AND end_time >= ? AND end_time <= ?
           AND end_time IS NOT NULL''',
        (prev_day_start_str, prev_day_end_str, day_start_str, day_end_str)
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
    
    # Nächtliches Aufwachen: Einträge, die am Tag gestartet haben
    # PERFORMANCE: Range-Query statt date()
    waking_rows = db.execute(
        '''SELECT id, start_time as timestamp, end_time 
           FROM night_waking 
           WHERE start_time >= ? AND start_time <= ?''',
        (day_start_str, day_end_str)
    ).fetchall()
    for row in waking_rows:
        entries.append({
            'id': row['id'],
            'category': 'night_waking',
            'timestamp': row['timestamp'],
            'end_time': row['end_time'],
            'display': 'Nächtliches Aufwachen'
        })
    
    # Nächtliches Aufwachen: Einträge, die am vorherigen Tag gestartet haben, aber am Tag enden
    # PERFORMANCE: Range-Query statt date()
    waking_rows_prev = db.execute(
        '''SELECT id, start_time as timestamp, end_time 
           FROM night_waking 
           WHERE start_time >= ? AND start_time <= ?
           AND end_time >= ? AND end_time <= ?
           AND end_time IS NOT NULL''',
        (prev_day_start_str, prev_day_end_str, day_start_str, day_end_str)
    ).fetchall()
    for row in waking_rows_prev:
        entries.append({
            'id': row['id'],
            'category': 'night_waking',
            'timestamp': row['timestamp'],
            'end_time': row['end_time'],
            'display': 'Nächtliches Aufwachen'
        })
    
    # Stillen
    # PERFORMANCE: Range-Query statt date() für bessere Index-Nutzung
    feeding_rows = db.execute(
        '''SELECT id, "feeding" as category, timestamp, side 
           FROM feeding 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (day_start_str, day_end_str)
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
    # PERFORMANCE: Range-Query statt date()
    bottle_rows = db.execute(
        '''SELECT id, "bottle" as category, timestamp, amount 
           FROM bottle 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (day_start_str, day_end_str)
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
    # PERFORMANCE: Range-Query statt date()
    diaper_rows = db.execute(
        '''SELECT id, "diaper" as category, timestamp, type 
           FROM diaper 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (day_start_str, day_end_str)
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
    # PERFORMANCE: Range-Query statt date()
    temp_rows = db.execute(
        '''SELECT id, "temperature" as category, timestamp, value 
           FROM temperature 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (day_start_str, day_end_str)
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
    # PERFORMANCE: Range-Query statt date()
    med_rows = db.execute(
        '''SELECT id, "medicine" as category, timestamp, name, dose 
           FROM medicine 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (day_start_str, day_end_str)
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

def get_all_entries_date_range(start_date, end_date):
    """
    PERFORMANCE-OPTIMIERUNG: Gibt alle Einträge für einen Datumsbereich zurück
    Statt get_all_entries_today() mehrmals aufzurufen, holen wir alle Daten in einer Query
    """
    db = get_db()
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)
    
    # Erweitere den Bereich um einen Tag vor/nach für Einträge, die über Mitternacht gehen
    extended_start = start_date - timedelta(days=1)
    extended_end = end_date + timedelta(days=1)
    
    range_start = datetime.combine(extended_start, datetime.min.time())
    range_end = datetime.combine(extended_end, datetime.max.time().replace(hour=23, minute=59, second=59))
    range_start_str = range_start.strftime('%Y-%m-%dT%H:%M:%S')
    range_end_str = range_end.strftime('%Y-%m-%dT%H:%M:%S')
    
    entries = []
    
    # PERFORMANCE: Eine Query für alle Schlaf-Einträge im Bereich
    sleep_rows = db.execute(
        '''SELECT id, "sleep" as category, type, start_time as timestamp, end_time 
           FROM sleep 
           WHERE (start_time >= ? AND start_time <= ?) 
           OR (end_time >= ? AND end_time <= ? AND end_time IS NOT NULL)''',
        (range_start_str, range_end_str, range_start_str, range_end_str)
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
    
    # Nächtliches Aufwachen im Bereich
    waking_rows = db.execute(
        '''SELECT id, start_time as timestamp, end_time 
           FROM night_waking 
           WHERE (start_time >= ? AND start_time <= ?)
           OR (end_time >= ? AND end_time <= ? AND end_time IS NOT NULL)''',
        (range_start_str, range_end_str, range_start_str, range_end_str)
    ).fetchall()
    for row in waking_rows:
        entries.append({
            'id': row['id'],
            'category': 'night_waking',
            'timestamp': row['timestamp'],
            'end_time': row['end_time'],
            'display': 'Nächtliches Aufwachen'
        })
    
    # Stillen im Bereich
    feeding_rows = db.execute(
        '''SELECT id, "feeding" as category, timestamp, side 
           FROM feeding 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (range_start_str, range_end_str)
    ).fetchall()
    for row in feeding_rows:
        entries.append({
            'id': row['id'],
            'category': 'feeding',
            'timestamp': row['timestamp'],
            'side': row['side'],
            'display': f"Stillen ({row['side']})"
        })
    
    # Flasche im Bereich
    bottle_rows = db.execute(
        '''SELECT id, "bottle" as category, timestamp, amount 
           FROM bottle 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (range_start_str, range_end_str)
    ).fetchall()
    for row in bottle_rows:
        entries.append({
            'id': row['id'],
            'category': 'bottle',
            'timestamp': row['timestamp'],
            'amount': row['amount'],
            'display': f"Flasche ({row['amount']} ml)"
        })
    
    # Windel im Bereich
    diaper_rows = db.execute(
        '''SELECT id, "diaper" as category, timestamp, type 
           FROM diaper 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (range_start_str, range_end_str)
    ).fetchall()
    for row in diaper_rows:
        entries.append({
            'id': row['id'],
            'category': 'diaper',
            'timestamp': row['timestamp'],
            'type': row['type'],
            'display': f"Windel ({row['type']})"
        })
    
    # Temperatur im Bereich
    temp_rows = db.execute(
        '''SELECT id, "temperature" as category, timestamp, value 
           FROM temperature 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (range_start_str, range_end_str)
    ).fetchall()
    for row in temp_rows:
        entries.append({
            'id': row['id'],
            'category': 'temperature',
            'timestamp': row['timestamp'],
            'value': row['value'],
            'display': f"Temperatur ({row['value']}°C)"
        })
    
    # Medizin im Bereich
    med_rows = db.execute(
        '''SELECT id, "medicine" as category, timestamp, name, dose 
           FROM medicine 
           WHERE timestamp >= ? AND timestamp <= ?''',
        (range_start_str, range_end_str)
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
    def get_name():
        """Holt den Namen des Babys"""
        db = get_db()
        row = db.execute('SELECT name FROM baby_info ORDER BY id LIMIT 1').fetchone()
        if row and row['name']:
            return row['name']
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
    def set_name(name):
        """Setzt den Namen des Babys"""
        db = get_db()
        # Prüfe ob bereits ein Eintrag existiert
        existing = db.execute('SELECT id FROM baby_info ORDER BY id LIMIT 1').fetchone()
        if existing:
            db.execute(
                'UPDATE baby_info SET name = ?, updated_at = ? WHERE id = ?',
                (name, datetime.now(tz_berlin).isoformat(), existing['id'])
            )
        else:
            db.execute(
                'INSERT INTO baby_info (name) VALUES (?)',
                (name,)
            )
        db.commit()
    
    @staticmethod
    def set_baby_info(name=None, birth_date=None):
        """Setzt Name und/oder Geburtsdatum des Babys"""
        db = get_db()
        existing = db.execute('SELECT id FROM baby_info ORDER BY id LIMIT 1').fetchone()
        updates = []
        values = []
        
        if name is not None:
            updates.append('name = ?')
            values.append(name)
        if birth_date is not None:
            updates.append('birth_date = ?')
            values.append(birth_date.isoformat())
        
        if updates:
            updates.append('updated_at = ?')
            values.append(datetime.now(tz_berlin).isoformat())
            
            if existing:
                values.append(existing['id'])
                db.execute(
                    f'UPDATE baby_info SET {", ".join(updates)} WHERE id = ?',
                    tuple(values)
                )
            else:
                # Wenn kein Eintrag existiert, erstelle einen
                if name is None:
                    name = ''
                if birth_date is None:
                    birth_date = date.today() - timedelta(days=180)  # Standard: 6 Monate
                db.execute(
                    'INSERT INTO baby_info (name, birth_date, updated_at) VALUES (?, ?, ?)',
                    (name, birth_date.isoformat(), datetime.now(tz_berlin).isoformat())
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
        """Gibt die empfohlenen Schlafzeiten basierend auf dem Alter zurück (nach Irina Kaiser / babyschlaffee.de)"""
        age_months = BabyInfo.get_age_months()
        
        # Empfohlene Schlafzeiten basierend auf Alter (nach Irina Kaiser)
        # Format: {'total': Gesamtschlaf, 'night': Nachtschlaf, 'day': Tagschlaf, 'naps': (min, max), 'wake_window': (min, max)}
        if age_months < 6:
            # Für Babys unter 6 Monaten: alte Werte beibehalten
            recommendations = {
                0: {'total': 16, 'night': 8.5, 'day': 8, 'naps': (3, 5), 'wake_window': (1.0, 1.5)},
                1: {'total': 15.5, 'night': 8.5, 'day': 7, 'naps': (3, 5), 'wake_window': (1.0, 1.5)},
                3: {'total': 15, 'night': 9.5, 'day': 4.5, 'naps': (2, 4), 'wake_window': (1.5, 2.0)},
                4: {'total': 15, 'night': 9.5, 'day': 4.5, 'naps': (3, 5), 'wake_window': (1.5, 2.0)},
                5: {'total': 15, 'night': 9.5, 'day': 4.5, 'naps': (2, 5), 'wake_window': (1.5, 2.5)},
            }
            age_keys = sorted([k for k in recommendations.keys() if k <= age_months], reverse=True)
            if age_keys:
                return recommendations[age_keys[0]]
        elif age_months <= 7:
            # 6-7 Monate: 2-3 Nickerchen, Tagschlaf 2-3,5h, Wachzeiten 2-3h, Nachtschlaf 10h (nach napper.app)
            return {'total': 14, 'night': 10, 'day': 2.75, 'naps': (2, 3), 'wake_window': (2.0, 3.0)}
        elif age_months <= 11:
            # 8-11 Monate: 2 Nickerchen, Tagschlaf 2-3h, Wachzeiten 3-3,5h
            return {'total': 13.5, 'night': 11, 'day': 2.5, 'naps': (2, 2), 'wake_window': (3.0, 3.5)}
        elif age_months <= 18:
            # 12-18 Monate: 1-2 Nickerchen, Tagschlaf 2-3h, Wachzeiten 3,5-4,5h
            return {'total': 13, 'night': 11, 'day': 2.5, 'naps': (1, 2), 'wake_window': (3.5, 4.5)}
        elif age_months <= 23:
            # 19-23 Monate: 1 Nickerchen, Tagschlaf 1-3h, Wachzeiten 4,5-5h
            return {'total': 12.5, 'night': 11, 'day': 2.0, 'naps': (1, 1), 'wake_window': (4.5, 5.0)}
        elif age_months <= 36:
            # 24-36 Monate: 1 Nickerchen, Tagschlaf 1-2h, Wachzeiten 5-6h
            return {'total': 12, 'night': 11, 'day': 1.5, 'naps': (1, 1), 'wake_window': (5.0, 6.0)}
        else:
            # Fallback für ältere Kinder
            return {'total': 11, 'night': 11, 'day': 1, 'naps': (0, 1), 'wake_window': (6.0, 7.0)}
    
    @staticmethod
    def get_nap_suggestions(selected_date=None):
        """Berechnet Vorschläge für das nächste Nickerchen"""
        if selected_date is None:
            selected_date = date.today()
        
        # Prüfe ob ein aktiver Schlaf existiert
        active_sleep = Sleep.get_active_sleep()
        if active_sleep:
            sleep_type = active_sleep.get('type')
            if sleep_type == 'nap':
                # Wenn ein Nickerchen aktiv ist, gib einen Hinweis zurück
                return [{'waiting_for_nap_end': True}]
            elif sleep_type == 'night':
                # Wenn Nachtschlaf aktiv ist und es ist heute, warte auf Aufwachen
                # Prüfe ob der Nachtschlaf heute gestartet wurde oder noch von gestern läuft
                try:
                    start_time_str = active_sleep.get('start_time')
                    if start_time_str:
                        start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_dt.tzinfo is None:
                            start_dt = tz_berlin.localize(start_dt.replace(tzinfo=None))
                        elif start_dt.tzinfo != tz_berlin:
                            start_dt = start_dt.astimezone(tz_berlin)
                        
                        # Wenn der Nachtschlaf heute gestartet wurde oder noch läuft und es ist heute,
                        # dann noch kein Nickerchen-Vorschlag
                        if start_dt.date() == selected_date or selected_date == date.today():
                            return [{'waiting_for_night_sleep_end': True}]
                except (ValueError, AttributeError):
                    # Bei Fehler, prüfe ob es heute ist
                    if selected_date == date.today():
                        return [{'waiting_for_night_sleep_end': True}]
        
        recommendations = BabyInfo.get_sleep_recommendations()
        min_naps, max_naps = recommendations['naps']
        # Berechne empfohlene Anzahl (Mittelwert, aufgerundet für bessere Empfehlung)
        # Bei 2-3 Nickerchen sollte 3 empfohlen werden, nicht 2
        avg_naps = (min_naps + max_naps) / 2
        target_naps = int(avg_naps + 0.5)  # Aufrunden wenn >= 0.5
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
        # WICHTIG: Berücksichtige sowohl Anzahl als auch Dauer!
        suggestions = []
        
        # Berechne verbleibende Tagschlafdauer
        remaining_day_sleep = target_day_sleep - total_day_sleep_hours
        
        # Hole die empfohlene Nachtschlaf-Zeit, um zu prüfen ob die Zeit bis dahin zu lang ist
        night_sleep_suggestion = BabyInfo.get_night_sleep_suggestion(selected_date)
        time_until_night_sleep_too_long = False
        
        if night_sleep_suggestion and not night_sleep_suggestion.get('waiting_for_night_sleep_end'):
            suggested_night_sleep_time = night_sleep_suggestion.get('suggested_time')
            if suggested_night_sleep_time:
                try:
                    if isinstance(suggested_night_sleep_time, str):
                        night_sleep_dt = datetime.fromisoformat(suggested_night_sleep_time.replace('Z', '+00:00'))
                    else:
                        night_sleep_dt = suggested_night_sleep_time
                    if night_sleep_dt.tzinfo is None:
                        night_sleep_dt = tz_berlin.localize(night_sleep_dt.replace(tzinfo=None))
                    elif night_sleep_dt.tzinfo != tz_berlin:
                        night_sleep_dt = night_sleep_dt.astimezone(tz_berlin)
                    
                    # Finde letztes Aufwachen für Berechnung
                    now = datetime.now(tz_berlin)
                    last_wake_time = None
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
                    
                    if not last_wake_time or last_wake_time.date() != selected_date:
                        last_wake_time = now
                    
                    # Berechne Zeit bis zum Nachtschlaf
                    hours_until_night_sleep = (night_sleep_dt - last_wake_time).total_seconds() / 3600.0
                    
                    # Hole maximale empfohlene Wachzeit für das Alter
                    age_months = BabyInfo.get_age_months()
                    recommendations = BabyInfo.get_sleep_recommendations()
                    min_wake_window, max_wake_window = recommendations.get('wake_window', (2.0, 3.0))
                    
                    # Wenn die Zeit bis zum Nachtschlaf länger als die maximale Wachzeit + 1 Stunde Puffer ist,
                    # sollte trotzdem ein Nickerchen empfohlen werden
                    max_acceptable_wake_time = max_wake_window + 1.0  # Puffer von 1 Stunde
                    if hours_until_night_sleep > max_acceptable_wake_time:
                        time_until_night_sleep_too_long = True
                except (ValueError, AttributeError, TypeError):
                    pass
        
        # Entscheidungskriterien für ein weiteres Nickerchen:
        # 1. Anzahl noch nicht erreicht UND
        #    (Verbleibende Tagschlafdauer > 0.5 Stunden ODER Zeit bis Nachtschlaf zu lang)
        # ODER
        # 2. Zeit bis zum Nachtschlaf ist zu lang (auch wenn Tagschlaf-Zeit erreicht)
        should_suggest_nap = (
            (completed_naps < target_naps) and (remaining_day_sleep > 0.5)
        ) or time_until_night_sleep_too_long
        
        if should_suggest_nap:
            # Berechne nächste empfohlene Zeit basierend auf letztem Aufwachen
            now = datetime.now(tz_berlin)
            last_wake_time = None
            
            # WICHTIG: Prüfe zuerst, ob ein aktiver Nachtschlaf existiert
            # Wenn ja und es ist heute, dann sollte noch kein Nickerchen-Vorschlag gemacht werden
            # Das erste Nickerchen wird erst nach dem Aufwachen berechnet
            if active_sleep and active_sleep.get('type') == 'night':
                try:
                    start_time_str = active_sleep.get('start_time')
                    if start_time_str:
                        start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_dt.tzinfo is None:
                            start_dt = tz_berlin.localize(start_dt.replace(tzinfo=None))
                        elif start_dt.tzinfo != tz_berlin:
                            start_dt = start_dt.astimezone(tz_berlin)
                        
                        # Wenn der Nachtschlaf heute noch läuft (gestartet heute oder gestern, aber noch aktiv),
                        # dann kein Nickerchen-Vorschlag bis zum Aufwachen
                        if selected_date == date.today():
                            return []
                except (ValueError, AttributeError):
                    # Bei Fehler, wenn es heute ist, kein Vorschlag
                    if selected_date == date.today():
                        return []
            
            # Finde letztes Aufwachen (Ende eines Nickerchens oder Nachtschlafs)
            # WICHTIG: Dies sollte das tatsächliche Ende eines Schlafs sein, nicht die aktuelle Zeit
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
            
            # Wenn kein Aufwachen heute gefunden wurde
            if not last_wake_time or last_wake_time.date() != selected_date:
                # Kein Aufwachen heute = kein Nickerchen-Vorschlag möglich
                # (Das erste Nickerchen wird erst nach dem Aufwachen aus dem Nachtschlaf berechnet)
                return []
            
            # Prüfe ob bereits ein Vorschlag für heute existiert (in der Datenbank gespeichert)
            # Dies verhindert, dass die Zeit nach hinten geschoben wird
            existing_suggestion = db.execute(
                '''SELECT suggested_time FROM nap_suggestions 
                   WHERE date = ? AND suggested_time > ? 
                   ORDER BY created_at DESC LIMIT 1''',
                (selected_date.isoformat(), now.isoformat())
            ).fetchone()
            
            if existing_suggestion:
                # Verwende die bereits berechnete Zeit (verhindert Verschiebung nach hinten)
                try:
                    suggested_time = datetime.fromisoformat(existing_suggestion['suggested_time'].replace('Z', '+00:00'))
                    if suggested_time.tzinfo is None:
                        suggested_time = tz_berlin.localize(suggested_time.replace(tzinfo=None))
                    # Prüfe ob die Zeit noch in der Zukunft liegt
                    if suggested_time > now:
                        # Verwende die alte Zeit, aber aktualisiere die restlichen Werte
                        # (z.B. wenn ein neues Nickerchen hinzugefügt wurde)
                        age_months = BabyInfo.get_age_months()
                        if age_months <= 3:
                            max_nap_duration = 1.5
                        elif age_months <= 6:
                            max_nap_duration = 1.5
                        elif age_months <= 12:
                            max_nap_duration = 1.0
                        else:
                            max_nap_duration = 1.0
                        
                        # Die tatsächliche Dauer sollte nicht die noch verfügbare Tagesschlafdauer überschreiten
                        # Verwende das Minimum aus altersbasierter Dauer und verfügbarer Dauer
                        # Aber mindestens 0.5 Stunden (30 Minuten)
                        nap_duration = min(max_nap_duration, max(remaining_day_sleep, 0.5))
                        
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
                except (ValueError, AttributeError):
                    # Falls Fehler beim Parsen, berechne neu
                    pass
            
            # Neue Berechnung (nur wenn noch kein Vorschlag existiert oder dieser in der Vergangenheit liegt)
            # Berechne tatsächliche Abstände zwischen bereits eingetragenen Nickerchen
            actual_wake_windows = []
            if len(naps_today) >= 2:
                # Sortiere Nickerchen nach Startzeit
                sorted_naps = []
                for nap in naps_today:
                    try:
                        start_dt = datetime.fromisoformat(nap['start_time'].replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(nap['end_time'].replace('Z', '+00:00'))
                        if start_dt.tzinfo is None:
                            start_dt = tz_berlin.localize(start_dt.replace(tzinfo=None))
                        if end_dt.tzinfo is None:
                            end_dt = tz_berlin.localize(end_dt.replace(tzinfo=None))
                        sorted_naps.append((start_dt, end_dt))
                    except (ValueError, AttributeError):
                        continue
                
                sorted_naps.sort(key=lambda x: x[0])  # Sortiere nach Startzeit
                
                # Berechne Abstände zwischen aufeinanderfolgenden Nickerchen
                for i in range(len(sorted_naps) - 1):
                    prev_end = sorted_naps[i][1]  # Ende des vorherigen Nickerchens
                    next_start = sorted_naps[i + 1][0]  # Start des nächsten Nickerchens
                    wake_window_hours = (next_start - prev_end).total_seconds() / 3600.0
                    if wake_window_hours > 0:  # Nur positive Abstände berücksichtigen
                        actual_wake_windows.append(wake_window_hours)
            
            # Berechne Durchschnitt der tatsächlichen Abstände
            avg_actual_wake_window = None
            if actual_wake_windows:
                avg_actual_wake_window = sum(actual_wake_windows) / len(actual_wake_windows)
            
            # Empfohlene Wachzeit vor nächstem Nickerchen (nach Irina Kaiser / babyschlaffee.de)
            recommendations = BabyInfo.get_sleep_recommendations()
            min_wake_window, max_wake_window = recommendations.get('wake_window', (2.0, 3.0))
            age_months = BabyInfo.get_age_months()
            
            # Verwende den Mittelwert der Wachzeit-Spanne als Basis (Tabellenwerte)
            base_wake_window = (min_wake_window + max_wake_window) / 2
            
            # Wenn tatsächliche Abstände vorhanden sind, verwende einen gewichteten Durchschnitt
            # 70% tatsächlicher Durchschnitt, 30% Tabellenwert (für Stabilität)
            if avg_actual_wake_window is not None:
                wake_window = avg_actual_wake_window * 0.7 + base_wake_window * 0.3
            else:
                # Keine tatsächlichen Abstände vorhanden, verwende Tabellenwerte mit Anpassungen
                # Anpassung basierend auf Tageszeit
                # Morgens (6-10 Uhr): längere Wachzeit (näher am Maximum, für besseren ersten Nickerchen)
                # Mittags (10-14 Uhr): mittlere Wachzeit (Mittelwert)
                # Nachmittags (14-18 Uhr): längere Wachzeit (näher am Maximum)
                current_hour = last_wake_time.hour
                if current_hour < 10:
                    # Morgens: verwende etwas über dem Minimum (für erstes Nickerchen)
                    # Für 6 Monate: min=2.0, max=3.0 -> 2.0 + (3.0-2.0)*0.25 = 2.25h ≈ 2h 15min
                    # Bei Aufwachen 06:20 → Nickerchen ca. 08:35 (Ziel: ~08:30)
                    wake_window = min_wake_window + (max_wake_window - min_wake_window) * 0.25
                elif current_hour < 14:
                    # Mittags: verwende den Mittelwert
                    wake_window = base_wake_window
                else:
                    # Nachmittags: verwende eher das Maximum
                    wake_window = min_wake_window + (max_wake_window - min_wake_window) * 0.8
            
            # Anpassung basierend auf Anzahl der bereits gemachten Nickerchen
            # Je mehr Nickerchen bereits gemacht wurden, desto länger die Wachzeit
            # Erhöhe die Wachzeit um 10-15% pro bereits gemachtem Nickerchen
            nap_adjustment = completed_naps * (max_wake_window - min_wake_window) * 0.15
            wake_window = wake_window + nap_adjustment
            
            # Stelle sicher, dass die Wachzeit innerhalb der empfohlenen Spanne bleibt
            # Erlaube aber auch etwas außerhalb, wenn tatsächliche Werte das nahelegen
            if avg_actual_wake_window is not None:
                # Wenn tatsächliche Werte vorhanden, erlaube mehr Flexibilität
                wake_window = max(min_wake_window * 0.8, min(wake_window, max_wake_window * 1.5))
            else:
                # Nur Tabellenwerte: strengere Grenzen
                wake_window = max(min_wake_window, min(wake_window, max_wake_window * 1.2))
            
            # Berechne nächste empfohlene Nickerchen-Zeit
            suggested_time = last_wake_time + timedelta(hours=wake_window)
            
            # Stelle sicher, dass die Zeit nicht in der Vergangenheit liegt
            if suggested_time < now:
                suggested_time = now + timedelta(minutes=15)  # Mindestens 15 Minuten ab jetzt
            
            # Empfohlene Dauer des Nickerchens basierend auf Alter
            if age_months <= 3:
                max_nap_duration = 1.5  # 1.5 Stunden
            elif age_months <= 6:
                max_nap_duration = 1.5  # 1.5 Stunden
            elif age_months <= 12:
                max_nap_duration = 1.0  # 1 Stunde
            else:
                max_nap_duration = 1.0  # 1 Stunde
            
            # Die tatsächliche Dauer sollte nicht die noch verfügbare Tagesschlafdauer überschreiten
            # Verwende das Minimum aus altersbasierter Dauer und verfügbarer Dauer
            # Aber mindestens 0.5 Stunden (30 Minuten)
            nap_duration = min(max_nap_duration, max(remaining_day_sleep, 0.5))
            
            # Speichere den Vorschlag in der Datenbank (verhindert Verschiebung nach hinten)
            try:
                # Lösche alte Vorschläge für heute
                db.execute('DELETE FROM nap_suggestions WHERE date = ?', (selected_date.isoformat(),))
                # Füge neuen Vorschlag hinzu
                db.execute(
                    '''INSERT INTO nap_suggestions (date, suggested_time, created_at) 
                       VALUES (?, ?, ?)''',
                    (selected_date.isoformat(), suggested_time.isoformat(), now.isoformat())
                )
                db.commit()
            except Exception:
                # Falls Tabelle noch nicht existiert, ignoriere Fehler
                pass
            
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
    
    @staticmethod
    def get_night_sleep_suggestion(selected_date=None):
        """Berechnet einen Vorschlag für die Nachtschlaf-Zeit basierend auf Alter und Schlafmustern"""
        if selected_date is None:
            selected_date = date.today()
        
        # Prüfe ob ein aktiver Nachtschlaf existiert
        active_sleep = Sleep.get_active_sleep()
        if active_sleep and active_sleep.get('type') == 'night':
            # Wenn Nachtschlaf aktiv ist, gib einen Hinweis zurück
            return {'waiting_for_night_sleep_end': True}
        
        recommendations = BabyInfo.get_sleep_recommendations()
        target_night_sleep = recommendations.get('night', 11.0)  # Standard: 11h
        target_day_sleep = recommendations.get('day', 3.0)
        
        db = get_db()
        now = datetime.now(tz_berlin)
        
        # Finde letztes Nachtschlaf-Aufwachen (PRIORITÄT: Nachtschlaf, nicht Nickerchen)
        # PERFORMANCE: Range-Query statt date() für bessere Index-Nutzung
        day_start = datetime.combine(selected_date, datetime.min.time())
        day_end = datetime.combine(selected_date, datetime.max.time().replace(hour=23, minute=59, second=59))
        day_start_str = day_start.strftime('%Y-%m-%dT%H:%M:%S')
        day_end_str = day_end.strftime('%Y-%m-%dT%H:%M:%S')
        
        last_night_sleep_end = db.execute(
            '''SELECT end_time FROM sleep 
               WHERE type = 'night'
               AND end_time IS NOT NULL 
               AND end_time >= ? AND end_time <= ?
               ORDER BY end_time DESC LIMIT 1''',
            (day_start_str, day_end_str)
        ).fetchone()
        
        # Falls kein Nachtschlaf-Aufwachen heute, suche nach dem letzten Nachtschlaf-Aufwachen generell
        if not last_night_sleep_end:
            last_night_sleep_end = db.execute(
                '''SELECT end_time FROM sleep 
                   WHERE type = 'night'
                   AND end_time IS NOT NULL 
                   ORDER BY end_time DESC LIMIT 1''',
            ).fetchone()
        
        # NEUE LOGIK: Berechne Einschlafzeit basierend auf aktuellem Zustand, nicht auf fester Aufwachzeit
        # Finde letztes Aufwachen für Wachzeit-Berechnung
        last_wake_time = None
        if last_sleep_end:
            try:
                last_wake_time = datetime.fromisoformat(last_sleep_end['end_time'].replace('Z', '+00:00'))
                if last_wake_time.tzinfo is None:
                    last_wake_time = tz_berlin.localize(last_wake_time.replace(tzinfo=None))
                elif last_wake_time.tzinfo != tz_berlin:
                    last_wake_time = last_wake_time.astimezone(tz_berlin)
            except (ValueError, AttributeError):
                pass
        
        # Wenn kein Aufwachen heute gefunden wurde, kann keine Berechnung gemacht werden
        if not last_wake_time or last_wake_time.date() != selected_date:
            # Für heute: verwende aktuelle Zeit als Basis (nur wenn es heute ist)
            if selected_date == date.today():
                last_wake_time = now
            else:
                # Für vergangene Tage ohne Aufwachen: kein Vorschlag möglich
                return {
                    'suggested_time': None,
                    'night_sleep_duration': adjusted_night_sleep,
                    'desired_wake_time': None,
                    'total_day_sleep': total_day_sleep_hours,
                    'target_day_sleep': target_day_sleep,
                    'remaining_day_sleep': remaining_day_sleep
                }
        
        # Für Wachzeit-Berechnung: Finde letztes Aufwachen (egal ob Nickerchen oder Nachtschlaf)
        # PERFORMANCE: Range-Query statt date()
        # WICHTIG: Dies wird jetzt oben verwendet, daher hier nur noch als Fallback
        if not last_wake_time:
            last_sleep_end = db.execute(
                '''SELECT end_time FROM sleep 
                   WHERE end_time IS NOT NULL 
                   AND end_time >= ? AND end_time <= ?
                   ORDER BY end_time DESC LIMIT 1''',
                (day_start_str, day_end_str)
            ).fetchone()
        else:
            last_sleep_end = None
        
        # Berechne bereits geschlafene Tagschlafdauer heute
        # PERFORMANCE: Range-Queries statt date() - nutzt Indizes besser
        prev_date = selected_date - timedelta(days=1)
        prev_day_start = datetime.combine(prev_date, datetime.min.time())
        prev_day_end = datetime.combine(prev_date, datetime.max.time().replace(hour=23, minute=59, second=59))
        prev_day_start_str = prev_day_start.strftime('%Y-%m-%dT%H:%M:%S')
        prev_day_end_str = prev_day_end.strftime('%Y-%m-%dT%H:%M:%S')
        
        naps_today = db.execute(
            '''SELECT start_time, end_time FROM sleep 
               WHERE type = 'nap' 
               AND end_time IS NOT NULL
               AND ((start_time >= ? AND start_time <= ?)
                    OR (start_time >= ? AND start_time <= ? 
                        AND end_time >= ? AND end_time <= ?))''',
            (day_start_str, day_end_str, prev_day_start_str, prev_day_end_str, day_start_str, day_end_str)
        ).fetchall()
        
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
        
        # Berechne verbleibende Tagschlafdauer
        remaining_day_sleep = target_day_sleep - total_day_sleep_hours
        
        # Berechne tatsächliche Nachtschlafdauern aus den letzten Nachtschläfen
        # Hole die letzten 7 Nachtschläfe (ca. eine Woche) für Durchschnittsberechnung
        recent_night_sleeps = db.execute(
            '''SELECT start_time, end_time FROM sleep 
               WHERE type = 'night' 
               AND end_time IS NOT NULL 
               AND start_time IS NOT NULL
               ORDER BY end_time DESC LIMIT 7'''
        ).fetchall()
        
        actual_night_sleep_durations = []
        for night_sleep in recent_night_sleeps:
            try:
                start_dt = datetime.fromisoformat(night_sleep['start_time'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(night_sleep['end_time'].replace('Z', '+00:00'))
                if start_dt.tzinfo is None:
                    start_dt = tz_berlin.localize(start_dt.replace(tzinfo=None))
                if end_dt.tzinfo is None:
                    end_dt = tz_berlin.localize(end_dt.replace(tzinfo=None))
                
                # Berechne Dauer (kann über Mitternacht gehen)
                if end_dt < start_dt:
                    # Endet am nächsten Tag
                    duration = (end_dt + timedelta(days=1) - start_dt).total_seconds() / 3600.0
                else:
                    duration = (end_dt - start_dt).total_seconds() / 3600.0
                
                # Ziehe nächtliches Aufwachen ab
                waking_duration = NightWaking.get_total_waking_duration(
                    night_sleep['start_time'], night_sleep['end_time']
                )
                duration = max(0, duration - waking_duration)
                
                if duration > 0 and duration < 16:  # Plausibilitätsprüfung (max 16h)
                    actual_night_sleep_durations.append(duration)
            except (ValueError, AttributeError):
                continue
        
        # Berechne Durchschnitt der tatsächlichen Nachtschlafdauern
        avg_actual_night_sleep = None
        if actual_night_sleep_durations:
            avg_actual_night_sleep = sum(actual_night_sleep_durations) / len(actual_night_sleep_durations)
        
        # Berechne die Nachtschlafdauer
        # Wenn tatsächliche Dauer vorhanden ist, verwende gewichteten Durchschnitt
        # 60% tatsächlicher Durchschnitt, 40% Tabellenwert (für Stabilität)
        if avg_actual_night_sleep is not None:
            adjusted_night_sleep = avg_actual_night_sleep * 0.6 + target_night_sleep * 0.4
        else:
            # Keine tatsächlichen Daten vorhanden, verwende Tabellenwert mit Anpassungen
            adjusted_night_sleep = target_night_sleep
        
        # Berechne Wachzeit seit letztem Aufwachen (für Übermüdungs-Bewertung)
        wake_duration = None
        if last_wake_time:
            wake_duration = (now - last_wake_time).total_seconds() / 3600.0
            
            # Wenn das Baby schon sehr lange wach ist (z.B. > 12h), 
            # sollte früher eingeschlafen werden (Übermüdung)
            # Dies wird bei der Einschlafzeit-Berechnung berücksichtigt
        
        # NEUE LOGIK: Berechne Einschlafzeit basierend auf aktuellem Zustand
        # Basis: Letztes Aufwachen + Wachzeit + Übermüdung + Tagschlaf-Status
        
        # Berechne empfohlene Einschlafzeit basierend auf:
        # 1. Aktueller Zeit (now)
        # 2. Wie lange ist das Baby schon wach? (wake_duration)
        # 3. Wie viel Tagschlaf fehlt noch? (remaining_day_sleep)
        # 4. Empfohlene Nachtschlafdauer (adjusted_night_sleep)
        
        # Startpunkt: Aktuelle Zeit
        base_sleep_time = now
        
        # Anpassung 1: Übermüdung (wenn sehr lange wach)
        if wake_duration is not None:
            if wake_duration > 12:
                # Sehr lange wach (>12h) - sollte früher schlafen
                # Reduziere die Zeit um bis zu 2 Stunden
                hours_to_subtract = min(2.0, (wake_duration - 12) * 0.3)
                base_sleep_time = base_sleep_time - timedelta(hours=hours_to_subtract)
            elif wake_duration > 10:
                # Lange wach (10-12h) - sollte etwas früher schlafen
                hours_to_subtract = (wake_duration - 10) * 0.2
                base_sleep_time = base_sleep_time - timedelta(hours=hours_to_subtract)
        
        # Anpassung 2: Tagschlaf-Status
        # Wenn noch viel Tagschlaf fehlt, könnte später schlafen (aber nicht zu spät)
        # Wenn genug Tagschlaf, kann früher schlafen
        if remaining_day_sleep > 1.0:
            # Noch viel Tagschlaf fehlt - könnte etwas später schlafen
            # Aber maximal bis 20:30 Uhr
            max_sleep_time = tz_berlin.localize(datetime.combine(selected_date, datetime.min.time().replace(hour=20, minute=30)))
            if base_sleep_time < max_sleep_time:
                # Erlaube bis zu 30 Minuten später, wenn noch viel Tagschlaf fehlt
                base_sleep_time = min(base_sleep_time + timedelta(minutes=30), max_sleep_time)
        elif remaining_day_sleep < 0.5:
            # Genug Tagschlaf - kann früher schlafen (wenn nicht schon zu spät)
            # Aber nicht vor 18:00 Uhr
            min_sleep_time = tz_berlin.localize(datetime.combine(selected_date, datetime.min.time().replace(hour=18, minute=0)))
            if base_sleep_time > min_sleep_time:
                # Erlaube bis zu 30 Minuten früher
                base_sleep_time = max(base_sleep_time - timedelta(minutes=30), min_sleep_time)
        
        # Anpassung 3: Tageszeit-basierte Grenzen
        # Nicht vor 17:00 Uhr (zu früh)
        min_sleep_time = tz_berlin.localize(datetime.combine(selected_date, datetime.min.time().replace(hour=17, minute=0)))
        if base_sleep_time < min_sleep_time:
            base_sleep_time = min_sleep_time
        
        # Nicht nach 21:30 Uhr (zu spät, außer bei Übermüdung)
        max_sleep_time = tz_berlin.localize(datetime.combine(selected_date, datetime.min.time().replace(hour=21, minute=30)))
        if wake_duration is None or wake_duration <= 12:
            # Nur begrenzen wenn nicht übermüdet
            if base_sleep_time > max_sleep_time:
                base_sleep_time = max_sleep_time
        
        suggested_sleep_time = base_sleep_time
        
        # Stelle sicher, dass die Zeit nicht zu weit in der Vergangenheit liegt
        # Mindestens 15 Minuten ab jetzt
        if suggested_sleep_time < now:
            suggested_sleep_time = now + timedelta(minutes=15)
        
        # Berechne erwartete Aufwachzeit basierend auf Einschlafzeit + Nachtschlafdauer
        # (nur für Anzeige, nicht für Berechnung verwendet)
        expected_wake_time = suggested_sleep_time + timedelta(hours=adjusted_night_sleep)
        
        return {
            'suggested_time': suggested_sleep_time,
            'night_sleep_duration': adjusted_night_sleep,
            'desired_wake_time': expected_wake_time,  # Erwartete Aufwachzeit (nur für Anzeige)
            'total_day_sleep': total_day_sleep_hours,
            'target_day_sleep': target_day_sleep,
            'remaining_day_sleep': remaining_day_sleep,
            'wake_duration': wake_duration  # Wie lange ist das Baby schon wach
        }

