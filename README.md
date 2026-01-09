# Baby-Tracking Web-App

Eine einfache, lokale Web-App zum Tracking von Baby-Aktivitäten wie Schlaf, Stillen, Flasche, Windel, Temperatur und Medizin.

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-sleepwalker86%2Fmybaby-blue)](https://hub.docker.com/r/sleepwalker86/mybaby)
[![GitHub](https://img.shields.io/badge/GitHub-sleepwalker86%2FmyBaby-black)](https://github.com/sleepwalker86/myBaby)

## Features

- **Schlaf-Tracking**: Nickerchen und Nachtschlaf mit Start-/Endzeit
- **Stillen**: Erfassung mit Brustseite (links/rechts)
- **Flasche**: Erfassung mit Menge in ml
- **Windel**: Erfassung mit Art (nass/groß/beides)
- **Temperatur**: Erfassung mit Temperaturwert
- **Medizin**: Erfassung mit Medikamentenname und Dosis
- **Tagesübersicht**: Dashboard mit aktuellen Status und letzten Einträgen
- **Mobile-first**: Optimiert für Smartphone-Nutzung mit großen Buttons

## Technischer Stack

- **Backend**: Python mit Flask
- **Frontend**: Server-Side Rendering mit HTML + Bootstrap 5
- **Datenbank**: SQLite
- **Deployment**: Docker

## Schnellstart

### Mit Docker Hub Image (empfohlen)

1. **App starten:**
   ```bash
   docker run -d \
     --name myBaby \
     -p 8000:8000 \
     -v $(pwd)/data:/data \
     sleepwalker86/mybaby:v1.0.0
   ```

2. **App öffnen:**
   Öffne im Browser: http://localhost:8000

3. **App stoppen:**
   ```bash
   docker stop myBaby
   docker rm myBaby
   ```

### Mit Docker Compose (lokal)

1. **App starten:**
   ```bash
   docker-compose up -d
   ```

2. **App öffnen:**
   Öffne im Browser: http://localhost:8000

3. **App stoppen:**
   ```bash
   docker-compose down
   ```

Die SQLite-Datenbank wird persistent im `./data` Verzeichnis gespeichert.

### Docker Hub

Das Image ist auf Docker Hub verfügbar:
- **Image**: `sleepwalker86/mybaby:v1.0.0`
- **Latest**: `sleepwalker86/mybaby:latest`
- **Multi-Architecture**: Unterstützt `linux/amd64` und `linux/arm64`

**Docker Hub Repository**: https://hub.docker.com/r/sleepwalker86/mybaby

### Ohne Docker (lokal)

1. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Umgebungsvariable setzen (optional):**
   ```bash
   export DATABASE_PATH=./data/baby_tracking.db
   ```

3. **App starten:**
   ```bash
   python main.py
   ```

4. **App öffnen:**
   Öffne im Browser: http://localhost:8000

## Projektstruktur

```
myBaby/
├── app/
│   ├── __init__.py          # Flask-App Factory
│   ├── models/
│   │   ├── database.py      # Datenbankverbindung
│   │   └── models.py        # Datenmodelle
│   ├── routes/
│   │   ├── main.py          # Hauptroute (Dashboard)
│   │   ├── sleep.py         # Schlaf-Routes
│   │   ├── feeding.py       # Stillen-Routes
│   │   ├── bottle.py        # Flasche-Routes
│   │   ├── diaper.py        # Windel-Routes
│   │   ├── temperature.py   # Temperatur-Routes
│   │   └── medicine.py      # Medizin-Routes
│   └── templates/
│       ├── base.html        # Base-Template
│       └── index.html       # Dashboard-Template
├── migrations/
│   └── 001_initial_schema.sql  # Datenbankschema
├── main.py                  # App-Einstiegspunkt
├── requirements.txt         # Python-Abhängigkeiten
├── Dockerfile              # Docker-Image Definition
├── docker-compose.yml      # Docker-Compose Konfiguration
└── README.md              # Diese Datei
```

## Datenbank

Die SQLite-Datenbank wird automatisch beim ersten Start erstellt. Das Schema wird über Migrationsskripte im `migrations/` Verzeichnis verwaltet.

### Tabellen

- `sleep`: Schlaf-Einträge (Nickerchen/Nachtschlaf)
- `feeding`: Stillen-Einträge
- `bottle`: Flaschen-Einträge
- `diaper`: Windel-Einträge
- `temperature`: Temperatur-Einträge
- `medicine`: Medizin-Einträge

## Verwendung

### Schnellaktionen

Die App ist für schnelle, einhändige Bedienung optimiert:

- **Schlaf**: Button für Nickerchen oder Nachtschlaf starten, Button zum Beenden erscheint automatisch
- **Stillen**: Direkte Buttons für links/rechts
- **Flasche**: Button öffnet Modal für Mengeneingabe
- **Windel**: Direkte Buttons für nass/groß/beides
- **Temperatur**: Button öffnet Modal für Temperatur-Eingabe
- **Medizin**: Button öffnet Modal für Name und Dosis

### Dashboard

Die Hauptseite zeigt:

- Aktuellen Schlafstatus (wach/schläft)
- Schlafdauer heute
- Letzte Stillzeit + Seite
- Letzte Flasche + Menge
- Letzte Windel
- Chronologische Liste aller heutigen Einträge

## Entwicklung

### Neue Migration hinzufügen

1. Erstelle eine neue SQL-Datei in `migrations/` mit fortlaufender Nummer (z.B. `002_add_field.sql`)
2. Die Migration wird beim nächsten App-Start automatisch ausgeführt

### Code-Struktur

- **Models**: Datenbankzugriff und Business-Logik
- **Routes**: HTTP-Endpunkte und Request-Handling
- **Templates**: HTML-Templates mit Jinja2

## Hinweise

- Die App ist für lokale Nutzung ohne Authentifizierung konzipiert
- Alle Zeitstempel werden in ISO-Format gespeichert
- Die Datenbank wird persistent gespeichert (auch bei Container-Neustart)
- Optimiert für mobile Nutzung (große Buttons, einhändige Bedienung)

## Lizenz

Privat / Eigengebrauch

