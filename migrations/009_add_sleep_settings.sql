-- Fügt Konfigurationsfelder für Schlaf-Einstellungen in baby_info hinzu

ALTER TABLE baby_info ADD COLUMN sleep_quality_options TEXT;
ALTER TABLE baby_info ADD COLUMN sleep_location_options TEXT;
ALTER TABLE baby_info ADD COLUMN default_sleep_quality TEXT;
ALTER TABLE baby_info ADD COLUMN default_sleep_location TEXT;

