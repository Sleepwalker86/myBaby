# Baby-Tracking Web-App

Eine einfache, lokale Web-App zum Tracking von Baby-Aktivitäten wie Schlaf, Stillen, Flasche, Windel, Temperatur und Medizin.

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-sleepwalker86%2Fmybaby-blue)](https://hub.docker.com/r/sleepwalker86/mybaby)
[![GitHub](https://img.shields.io/badge/GitHub-sleepwalker86%2FmyBaby-black)](https://github.com/sleepwalker86/myBaby)

## Features

### 📱 Hauptfunktionen

- **Schlaf-Tracking**: Erfasse Nickerchen und Nachtschlaf mit automatischer Dauerberechnung
- **Nächtliches Aufwachen**: Dokumentiere nächtliche Wachphasen, die automatisch vom Nachtschlaf abgezogen werden
- **Intelligente Schlaf-Vorschläge**: Die App berechnet basierend auf Alter und Schlafmustern, wann das nächste Nickerchen und der optimale Nachtschlaf ansteht
- **Circular Timeline**: Visualisiere den Tagesverlauf als übersichtliches Kreisdiagramm
- **Stillen & Flasche**: Tracke Stillzeiten (links/rechts) mit optionaler Endzeit und Flaschenmengen
- **Windel-Tracking**: Dokumentiere Windelwechsel (nass/groß/beides)
- **Temperatur & Medizin**: Erfasse Fieberwerte und Medikamentengaben
- **Einträge-Übersicht**: Sieh alle Einträge in Tages- oder Wochenansicht
- **Trends & Statistiken**: Analysiere Schlafmuster, Windel- und Still-Statistiken
- **Mehrsprachigkeit**: Unterstützung für Deutsch, Englisch und Spanisch
- **Dark Mode**: Schonende Darstellung für die Nacht

### 🎯 Besondere Features

- **Intelligente Schlaf-Vorschläge**: Basierend auf wissenschaftlichen Empfehlungen (babyschlaffee.de) und dem Alter deines Babys. Berücksichtigt auch tatsächliche Schlafmuster aus der Vergangenheit
- **Visuelles Timeline-Diagramm**: 24-Stunden-Übersicht mit allen Aktivitäten auf einen Blick
- **Quick Entry**: Plus-Button oben auf dem Dashboard für schnellen Zugriff auf alle Eintragsmöglichkeiten
- **Mobile-optimiert**: Große Buttons für einfache, einhändige Bedienung
- **Persönlich**: Gib deinem Baby einen Namen - die App wird persönlicher
- **Lokal & sicher**: Alle Daten bleiben auf deinem Gerät, keine Cloud, keine Anmeldung

## Technischer Stack

- **Backend**: Python mit Flask
- **Frontend**: Server-Side Rendering mit HTML + Bootstrap 5
- **Datenbank**: SQLite
- **Internationalisierung**: JSON-basierte Mehrsprachigkeit (Deutsch, Englisch, Spanisch)
- **Deployment**: Docker

## Schnellstart

### Mit Docker Hub Image (empfohlen)

1. **App starten:**
   ```bash
   docker run -d \
     --name myBaby \
     -p 8000:8000 \
     -v $(pwd)/data:/data \
     sleepwalker86/mybaby:latest
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
- **Image**: `sleepwalker86/mybaby:latest`
- **Multi-Architecture**: Unterstützt `linux/amd64` und `linux/arm64`

**Docker Hub Repository**: https://hub.docker.com/r/sleepwalker86/mybaby

## Erste Schritte

### 1. Einstellungen konfigurieren

Gehe zu **Einstellungen** und trage ein:
- **Name des Babys** (optional, macht die App persönlicher)
- **Geburtsdatum** (wichtig für die Schlaf-Vorschläge)
- **Sprache**: Wähle zwischen Deutsch, Englisch oder Spanisch
- **Dark Mode**: Aktiviere für schonende Nutzung in der Nacht

### 2. Erste Einträge erfassen

Auf dem **Dashboard** findest du große Buttons für alle Aktivitäten:

- **Plus-Button** (oben rechts): Öffnet ein Modal mit allen Eintragsmöglichkeiten
- **Schlaf**: Starte ein Nickerchen oder den Nachtschlaf. Die App stoppt automatisch die Zeit.
- **Nächtliches Aufwachen**: Dokumentiere Wachphasen in der Nacht (wird automatisch vom Nachtschlaf abgezogen)
- **Stillen**: Wähle links oder rechts. Optional kannst du eine Endzeit eintragen, um die Stilldauer zu dokumentieren.
- **Flasche**: Gib die Menge in ml ein
- **Windel**: Wähle nass, groß oder beides
- **Temperatur**: Trage die gemessene Temperatur ein
- **Medizin**: Erfasse Medikamentenname und Dosis

### 3. Dashboard verstehen

Das Dashboard zeigt dir:

- **Aktueller Status**: Ist das Baby wach oder schläft es gerade?
- **Schlafdauer heute**: Gesamte Schlafzeit (Nachtschlaf + Nickerchen)
- **Letzte Aktivitäten**: Wann war das letzte Stillen, die letzte Flasche, etc.
- **Circular Timeline**: Visuelle Darstellung des Tagesverlaufs
- **Schlaf-Vorschläge**: Wann das nächste Nickerchen und der optimale Nachtschlaf empfohlen werden
- **Heutige Einträge**: Chronologische Liste aller Aktivitäten

## Projektstruktur

```
myBaby/
├── app/
│   ├── __init__.py          # Flask-App Factory
│   ├── i18n.py              # Internationalisierung (Mehrsprachigkeit)
│   ├── models/
│   │   ├── database.py      # Datenbankverbindung
│   │   └── models.py         # Datenmodelle & Business-Logik
│   ├── routes/
│   │   ├── main.py          # Hauptroute (Dashboard)
│   │   ├── sleep.py         # Schlaf-Routes
│   │   ├── feeding.py       # Stillen-Routes
│   │   ├── bottle.py        # Flasche-Routes
│   │   ├── diaper.py        # Windel-Routes
│   │   ├── temperature.py   # Temperatur-Routes
│   │   ├── medicine.py      # Medizin-Routes
│   │   ├── edit.py          # Bearbeiten/Löschen von Einträgen
│   │   ├── trends.py        # Trends & Statistiken
│   │   ├── entries.py       # Einträge-Übersicht (Tag/Woche)
│   │   ├── settings.py      # Einstellungen
│   │   └── i18n.py          # Sprachumschaltung
│   └── templates/
│       ├── base.html        # Base-Template
│       ├── index.html       # Dashboard-Template
│       ├── entries.html    # Einträge-Template
│       ├── trends.html      # Trends-Template
│       └── settings.html    # Einstellungen-Template
├── translations/
│   ├── de.json              # Deutsche Übersetzungen
│   ├── en.json              # Englische Übersetzungen
│   └── es.json              # Spanische Übersetzungen
├── migrations/
│   └── 001_initial_schema.sql  # Datenbankschema
├── main.py                  # App-Einstiegspunkt
├── requirements.txt         # Python-Abhängigkeiten
├── Dockerfile              # Docker-Image Definition
├── docker-compose.yml      # Docker-Compose Konfiguration
└── README.md              # Vollständige Dokumentation
```

## Datenbank

Die SQLite-Datenbank wird automatisch beim ersten Start erstellt. Das Schema wird über Migrationsskripte im `migrations/` Verzeichnis verwaltet.

### Tabellen

- `baby_info`: Baby-Informationen (Name, Geburtsdatum)
- `sleep`: Schlaf-Einträge (Nickerchen/Nachtschlaf)
- `night_waking`: Nächtliches Aufwachen
- `feeding`: Stillen-Einträge
- `bottle`: Flaschen-Einträge
- `diaper`: Windel-Einträge
- `temperature`: Temperatur-Einträge
- `medicine`: Medizin-Einträge

## Verwendung

### Schnellaktionen

Die App ist für schnelle, einhändige Bedienung optimiert:

- **Quick Entry**: Plus-Button oben rechts öffnet ein Modal mit allen Eintragsmöglichkeiten
- **Schlaf**: Button für Nickerchen oder Nachtschlaf starten, Button zum Beenden erscheint automatisch
- **Nächtliches Aufwachen**: Dokumentiere Wachphasen in der Nacht
- **Stillen**: Direkte Buttons für links/rechts, optional mit Endzeit
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
- Circular Timeline mit allen Aktivitäten des Tages
- Schlaf-Vorschläge (Nickerchen + Nachtschlaf)
- Chronologische Liste aller heutigen Einträge

### Einträge durchsuchen

Die Seite **Einträge** bietet:

- **Tagesansicht**: Alle Einträge eines bestimmten Tages
- **Wochenansicht**: Übersicht über eine ganze Woche, gruppiert nach Tagen
- **Navigation**: Blättere zwischen Tagen und Wochen

### Trends & Statistiken

Die Seite **Trends** zeigt:

- Gesamtschlaf und durchschnittlichen täglichen Schlaf
- Durchschnittliche Aufwach- und Einschlafzeiten
- Windel-Statistiken (Ø Gesamt, Nass, Groß)
- Still-Statistiken (Ø Einträge pro Tag)
- Schlafverteilung (Nachtschlaf vs. Nickerchen)
- Temperaturverlauf
- Interaktive Charts für alle Statistiken

## Entwicklung

### Neue Migration hinzufügen

1. Erstelle eine neue SQL-Datei in `migrations/` mit fortlaufender Nummer (z.B. `002_add_field.sql`)
2. Die Migration wird beim nächsten App-Start automatisch ausgeführt

### Code-Struktur

- **Models**: Datenbankzugriff und Business-Logik (inkl. Schlaf-Vorschläge)
- **Routes**: HTTP-Endpunkte und Request-Handling
- **Templates**: HTML-Templates mit Jinja2
- **i18n**: JSON-basierte Mehrsprachigkeit

### Neue Sprache hinzufügen

1. Erstelle eine neue JSON-Datei in `translations/` (z.B. `fr.json`)
2. Füge die Sprache zu `SUPPORTED_LANGUAGES` in `app/i18n.py` hinzu
3. Füge einen Button in `app/templates/settings.html` hinzu

## Hinweise

- Die App ist für lokale Nutzung ohne Authentifizierung konzipiert
- Alle Zeitstempel werden in ISO-Format gespeichert
- Die Datenbank wird persistent gespeichert (auch bei Container-Neustart)
- Optimiert für mobile Nutzung (große Buttons, einhändige Bedienung)
- Unterstützt Dark Mode für schonende Nutzung in der Nacht
- Mehrsprachig: Deutsch (Standard), Englisch, Spanisch

## Häufige Fragen

**Wie funktionieren die Schlaf-Vorschläge?**
Die App nutzt wissenschaftlich fundierte Empfehlungen basierend auf dem Alter deines Babys. Sie berücksichtigt bereits gemachte Nickerchen, die Tageszeit und die noch empfohlene Tagschlafdauer. Für Nachtschlaf-Vorschläge werden auch die tatsächlichen Schlafmuster der letzten Tage berücksichtigt.

**Kann ich Einträge bearbeiten?**
Ja, alle Einträge können nachträglich bearbeitet oder gelöscht werden.

**Funktioniert die App offline?**
Ja, sobald die App gestartet ist, funktioniert sie komplett offline. Nur für den ersten Start (Docker-Image herunterladen) wird Internet benötigt.

**Wo werden die Daten gespeichert?**
Alle Daten werden lokal in einer SQLite-Datenbank gespeichert. Bei Docker-Nutzung im `./data` Verzeichnis.

**Welche Sprachen werden unterstützt?**
Die App unterstützt Deutsch (Standard), Englisch und Spanisch. Die Sprache kann in den Einstellungen umgeschaltet werden.

## Lizenz / Nutzung

© 2025 Sascha Moritz

Der Quellcode darf für den **eigenen Gebrauch** angepasst und erweitert werden.

Eine **Weitergabe, Veröffentlichung oder kommerzielle Nutzung veränderter Versionen ist nicht gestattet**.

Wenn du den Code in einem anderen Kontext einsetzen willst (z. B. in einem Unternehmen oder als Open‑Source‑Projekt), kläre dies bitte vorher mit dem Autor.

---

## Haftungsausschluss

Dieses Projekt wird ohne Garantie bereitgestellt. Es gibt keine Gewähr für Richtigkeit, Vollständigkeit oder Eignung für einen bestimmten Zweck. Die Nutzung erfolgt auf eigene Verantwortung – insbesondere im Hinblick auf den Umgang mit sensiblen Daten.

