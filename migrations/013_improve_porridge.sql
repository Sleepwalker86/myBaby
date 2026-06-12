-- Migration 013: Porridge-Tabelle verbessern
CREATE INDEX IF NOT EXISTS idx_porridge_timestamp ON porridge(timestamp);
