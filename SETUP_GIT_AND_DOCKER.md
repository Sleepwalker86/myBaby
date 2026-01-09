# Setup-Anleitung: Git Repository und Docker Hub

## Schritt 1: Git Repository initialisieren

```bash
# Repository initialisieren
git init

# Git-Konfiguration (optional, falls noch nicht gesetzt)
git config user.name "sleepwalker86"
git config user.email "sascha.moritz@web.de"

# Alle Dateien hinzufügen
git add .

# Erster Commit
git commit -m "Initial commit: Baby-Tracking App v1.0.0"

# Tag für Version v1.0.0 erstellen
git tag v1.0.0
```

## Schritt 2: GitHub Repository erstellen

1. Gehe zu https://github.com/new
2. Repository-Name: `myBaby`
3. Beschreibung: "Baby-Tracking Web-App"
4. **Wichtig**: Repository als **öffentlich** markieren
5. Klicke auf "Create repository"

## Schritt 3: GitHub Repository verbinden

```bash
# Remote Repository hinzufügen (ersetze USERNAME falls nötig)
git remote add origin https://github.com/sleepwalker86/myBaby.git

# Branch auf main setzen
git branch -M main

# Code und Tags pushen
git push -u origin main
git push origin v1.0.0
```

## Schritt 4: Docker Hub Login

```bash
# Bei Docker Hub einloggen
docker login

# Username: sleepwalker86
# Password: Dein Docker Hub Passwort oder Access Token
```

## Schritt 5: Multi-Architecture Build und Push

### Option A: Mit Build-Skript (empfohlen)

```bash
# Skript ausführbar machen (falls noch nicht geschehen)
chmod +x build-and-push.sh

# Build und Push ausführen
./build-and-push.sh
```

### Option B: Manuell

```bash
# Prüfe ob Docker Buildx verfügbar ist
docker buildx version

# Erstelle einen neuen Builder für Multi-Architecture
docker buildx create --name mybaby-builder --use
docker buildx inspect --bootstrap

# Build und Push für Multi-Architecture (amd64, arm64)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag sleepwalker86/mybaby:v1.0.0 \
  --tag sleepwalker86/mybaby:latest \
  --push \
  .
```

## Schritt 6: GitHub Actions Secrets konfigurieren (optional)

Für automatische Builds bei neuen Tags:

1. Gehe zu: https://github.com/sleepwalker86/myBaby/settings/secrets/actions
2. Klicke auf "New repository secret"
3. Erstelle zwei Secrets:
   - **Name**: `DOCKER_USERNAME`, **Value**: `sleepwalker86`
   - **Name**: `DOCKER_PASSWORD`, **Value**: Dein Docker Hub Access Token

   (Docker Hub Access Token erstellen: https://hub.docker.com/settings/security)

## Schritt 7: Verifizierung

### Docker Hub
- Öffne: https://hub.docker.com/r/sleepwalker86/mybaby
- Prüfe, ob die Tags `v1.0.0` und `latest` vorhanden sind
- Prüfe, ob Multi-Architecture Support aktiviert ist (amd64, arm64)

### GitHub
- Öffne: https://github.com/sleepwalker86/myBaby
- Prüfe, ob alle Dateien vorhanden sind
- Prüfe, ob der Tag `v1.0.0` vorhanden ist

## Test des Docker Hub Images

```bash
# Lokales Image entfernen (falls vorhanden)
docker rmi sleepwalker86/mybaby:v1.0.0 2>/dev/null || true

# Image von Docker Hub pullen
docker pull sleepwalker86/mybaby:v1.0.0

# Container starten
docker run -d \
  --name myBaby-test \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  sleepwalker86/mybaby:v1.0.0

# Testen: http://localhost:8000

# Container stoppen und entfernen
docker stop myBaby-test
docker rm myBaby-test
```

## Nächste Schritte

- Bei neuen Versionen: Tag erstellen und pushen
- GitHub Actions baut automatisch (wenn Secrets konfiguriert)
- Oder manuell: `./build-and-push.sh` ausführen

## Troubleshooting

### Docker Buildx nicht verfügbar
```bash
# Docker Desktop sollte Buildx bereits enthalten
# Falls nicht, installiere Docker Buildx Plugin
```

### Permission Denied bei Git
```bash
# Prüfe Git-Konfiguration
git config --global user.name
git config --global user.email
```

### Docker Hub Login fehlgeschlagen
- Verwende einen Access Token statt Passwort
- Erstelle Token: https://hub.docker.com/settings/security

