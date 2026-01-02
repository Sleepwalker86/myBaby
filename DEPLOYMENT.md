# Deployment Guide

## Docker Hub Push (Multi-Architecture)

### Voraussetzungen

1. Docker Buildx installiert (normalerweise bereits in Docker Desktop enthalten)
2. Docker Hub Account: `sleepwalker86`
3. Bei Docker Hub eingeloggt: `docker login`

### Manueller Build und Push

1. **Build-Skript ausführen:**
   ```bash
   ./build-and-push.sh
   ```

   Das Skript:
   - Erstellt einen Multi-Architecture Builder (falls nicht vorhanden)
   - Baut das Image für `linux/amd64` und `linux/arm64`
   - Taggt als `sleepwalker86/myBaby:v1.0.0` und `sleepwalker86/myBaby:latest`
   - Pusht beide Tags zu Docker Hub

### Manueller Build (ohne Skript)

```bash
# Builder erstellen (einmalig)
docker buildx create --name mybaby-builder --use
docker buildx inspect --bootstrap

# Build und Push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag sleepwalker86/myBaby:v1.0.0 \
  --tag sleepwalker86/myBaby:latest \
  --push \
  .
```

### GitHub Actions (Automatisch)

Bei jedem Git Tag (z.B. `v1.0.0`) wird automatisch ein Build und Push ausgelöst.

**Voraussetzungen:**
1. GitHub Repository Secrets konfigurieren:
   - `DOCKER_USERNAME`: `sleepwalker86`
   - `DOCKER_PASSWORD`: Docker Hub Access Token

2. Tag erstellen und pushen:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

## Git Repository Setup

### Initialisierung

```bash
# Repository initialisieren
git init

# Alle Dateien hinzufügen
git add .

# Erster Commit
git commit -m "Initial commit: Baby-Tracking App v1.0.0"

# Remote Repository hinzufügen (GitHub)
git remote add origin https://github.com/sleepwalker86/myBaby.git

# Branch auf main setzen
git branch -M main

# Ersten Push
git push -u origin main
```

### Tag erstellen

```bash
# Tag für Version v1.0.0
git tag v1.0.0

# Tag pushen
git push origin v1.0.0
```

## Docker Hub Repository

- **Repository**: https://hub.docker.com/r/sleepwalker86/myBaby
- **Tags**: 
  - `v1.0.0` - Version 1.0.0
  - `latest` - Neueste Version

## Verwendung des Docker Hub Images

```bash
# Image pullen
docker pull sleepwalker86/myBaby:v1.0.0

# Container starten
docker run -d \
  --name myBaby \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  sleepwalker86/myBaby:v1.0.0
```

## Multi-Architecture Support

Das Image unterstützt:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, z.B. Apple Silicon, Raspberry Pi 4+)

Docker wählt automatisch die passende Architektur für dein System.

