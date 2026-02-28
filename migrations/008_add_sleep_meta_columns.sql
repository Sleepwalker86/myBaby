-- Fügt zusätzliche Metadaten-Spalten für Schlaf-Einträge hinzu

ALTER TABLE sleep ADD COLUMN sleep_quality TEXT;
ALTER TABLE sleep ADD COLUMN sleep_location TEXT;

