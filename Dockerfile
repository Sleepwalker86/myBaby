FROM python:3.11-slim

WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# Port freigeben
EXPOSE 8000

# Umgebungsvariable für Datenbankpfad
ENV DATABASE_PATH=/data/baby_tracking.db

# App starten
CMD ["python", "main.py"]

