#!/usr/bin/env python3
"""Script zum Generieren von Testdaten für die Baby-Tracking App"""
import sqlite3
import random
from datetime import datetime, timedelta, date
import os

# Datenbankpfad
DB_PATH = os.environ.get('DATABASE_PATH', '/data/baby_tracking.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Verbindung zur Datenbank
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Tabellen erstellen falls nicht vorhanden
migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
if os.path.exists(os.path.join(migrations_dir, '001_initial_schema.sql')):
    with open(os.path.join(migrations_dir, '001_initial_schema.sql'), 'r', encoding='utf-8') as f:
        sql = f.read()
        cursor.executescript(sql)
    conn.commit()

# Bestehende Daten löschen (optional - auskommentieren wenn Daten behalten werden sollen)
cursor.execute('DELETE FROM sleep')
cursor.execute('DELETE FROM feeding')
cursor.execute('DELETE FROM bottle')
cursor.execute('DELETE FROM diaper')
cursor.execute('DELETE FROM temperature')
cursor.execute('DELETE FROM medicine')
conn.commit()

# Zeitraum: Letzte 10 Tage
today = date.today()
start_date = today - timedelta(days=10)

# Hilfsfunktionen
def random_time_between(start_hour, end_hour, base_date):
    """Generiert eine zufällige Zeit zwischen zwei Stunden"""
    hour = random.randint(start_hour, end_hour)
    minute = random.randint(0, 59)
    return datetime.combine(base_date, datetime.min.time().replace(hour=hour, minute=minute))

def add_sleep_entry(sleep_type, start_time, end_time=None):
    """Fügt einen Schlaf-Eintrag hinzu"""
    cursor.execute(
        'INSERT INTO sleep (type, start_time, end_time) VALUES (?, ?, ?)',
        (sleep_type, start_time.isoformat(), end_time.isoformat() if end_time else None)
    )

def add_feeding_entry(timestamp, side):
    """Fügt einen Still-Eintrag hinzu"""
    cursor.execute(
        'INSERT INTO feeding (timestamp, side) VALUES (?, ?)',
        (timestamp.isoformat(), side)
    )

def add_bottle_entry(timestamp, amount):
    """Fügt einen Flaschen-Eintrag hinzu"""
    cursor.execute(
        'INSERT INTO bottle (timestamp, amount) VALUES (?, ?)',
        (timestamp.isoformat(), amount)
    )

def add_diaper_entry(timestamp, diaper_type):
    """Fügt einen Windel-Eintrag hinzu"""
    cursor.execute(
        'INSERT INTO diaper (timestamp, type) VALUES (?, ?)',
        (timestamp.isoformat(), diaper_type)
    )

def add_temperature_entry(timestamp, value):
    """Fügt einen Temperatur-Eintrag hinzu"""
    cursor.execute(
        'INSERT INTO temperature (timestamp, value) VALUES (?, ?)',
        (timestamp.isoformat(), value)
    )

def add_medicine_entry(timestamp, name, dose):
    """Fügt einen Medizin-Eintrag hinzu"""
    cursor.execute(
        'INSERT INTO medicine (timestamp, name, dose) VALUES (?, ?, ?)',
        (timestamp.isoformat(), name, dose)
    )

# Testdaten generieren
print("Generiere Testdaten...")

for day_offset in range(10):
    current_date = start_date + timedelta(days=day_offset)
    
    # Schlaf-Einträge
    # Nachtschlaf: ca. 20:00 - 07:00 (mit Variation)
    night_start = random_time_between(19, 21, current_date)
    night_end = random_time_between(6, 8, current_date + timedelta(days=1))
    add_sleep_entry('night', night_start, night_end)
    
    # 2-3 Nickerchen pro Tag
    num_naps = random.randint(2, 3)
    last_nap_end = night_start
    
    for nap_num in range(num_naps):
        # Nickerchen startet 1-3 Stunden nach letztem Schlafende
        nap_start = last_nap_end + timedelta(hours=random.uniform(1, 3))
        # Nickerchen dauert 30-120 Minuten
        nap_duration = random.uniform(30, 120)
        nap_end = nap_start + timedelta(minutes=nap_duration)
        
        # Sicherstellen, dass nicht nach Mitternacht
        if nap_end.date() > current_date:
            nap_end = datetime.combine(current_date, datetime.max.time().replace(hour=23, minute=59))
        
        add_sleep_entry('nap', nap_start, nap_end)
        last_nap_end = nap_end
    
    # Stillen: 6-10 mal pro Tag
    num_feedings = random.randint(6, 10)
    last_feeding = night_end
    
    for _ in range(num_feedings):
        # Stillen alle 2-4 Stunden
        feeding_time = last_feeding + timedelta(hours=random.uniform(2, 4))
        if feeding_time.date() > current_date:
            break
        side = random.choice(['links', 'rechts'])
        add_feeding_entry(feeding_time, side)
        last_feeding = feeding_time
    
    # Flasche: 1-3 mal pro Tag (wenn nicht gestillt wird)
    num_bottles = random.randint(1, 3)
    for _ in range(num_bottles):
        bottle_time = random_time_between(8, 22, current_date)
        amount = random.choice([60, 80, 100, 120, 150])
        add_bottle_entry(bottle_time, amount)
    
    # Windel: 4-8 mal pro Tag
    num_diapers = random.randint(4, 8)
    for _ in range(num_diapers):
        diaper_time = random_time_between(6, 23, current_date)
        diaper_type = random.choice(['nass', 'groß', 'beides'])
        add_diaper_entry(diaper_time, diaper_type)
    
    # Temperatur: 1-2 mal pro Tag (nicht jeden Tag)
    if random.random() < 0.7:  # 70% Chance
        num_temps = random.randint(1, 2)
        for _ in range(num_temps):
            temp_time = random_time_between(8, 20, current_date)
            # Normale Temperatur: 36.5 - 37.5°C, manchmal leicht erhöht
            if random.random() < 0.1:  # 10% Chance für leicht erhöhte Temperatur
                temp_value = round(random.uniform(37.6, 38.2), 1)
            else:
                temp_value = round(random.uniform(36.5, 37.5), 1)
            add_temperature_entry(temp_time, temp_value)
    
    # Medizin: selten (nur an 2-3 Tagen)
    if random.random() < 0.3:  # 30% Chance
        med_time = random_time_between(8, 20, current_date)
        medicines = [
            ('Paracetamol', '2.5ml'),
            ('Ibuprofen', '2ml'),
            ('Vitamin D', '1 Tropfen'),
            ('Fenistil', '3 Tropfen')
        ]
        name, dose = random.choice(medicines)
        add_medicine_entry(med_time, name, dose)

conn.commit()
print(f"Testdaten erfolgreich generiert! ({cursor.rowcount} Einträge)")
print(f"Datenbank: {DB_PATH}")

# Statistik ausgeben
cursor.execute('SELECT COUNT(*) FROM sleep')
sleep_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM feeding')
feeding_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM bottle')
bottle_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM diaper')
diaper_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM temperature')
temp_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM medicine')
med_count = cursor.fetchone()[0]

total = sleep_count + feeding_count + bottle_count + diaper_count + temp_count + med_count
print(f"\nStatistik:")
print(f"  Schlaf: {sleep_count}")
print(f"  Stillen: {feeding_count}")
print(f"  Flasche: {bottle_count}")
print(f"  Windel: {diaper_count}")
print(f"  Temperatur: {temp_count}")
print(f"  Medizin: {med_count}")
print(f"  Gesamt: {total}")

conn.close()

