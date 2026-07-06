-- Migration 018: Geschlecht des Babys (Voraussetzung für WHO-Perzentilkurven)
-- Nullable, da Bestandsinstallationen noch keinen Wert haben; das Perzentil-Feature
-- bleibt einfach ausgeblendet, solange gender IS NULL.
ALTER TABLE baby_info ADD COLUMN gender TEXT CHECK(gender IN ('m', 'f'));
