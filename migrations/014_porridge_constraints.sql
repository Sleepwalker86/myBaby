-- Migration 014: Porridge created_at Spalte hinzufügen
-- CHECK-Constraints können in SQLite nicht nachträglich via ALTER TABLE ergänzt werden,
-- daher nur created_at als neue Spalte.
ALTER TABLE porridge ADD COLUMN created_at TEXT DEFAULT (datetime('now'));
