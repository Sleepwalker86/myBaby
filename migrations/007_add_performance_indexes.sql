-- Performance-Optimierungen: Zusätzliche Indizes für häufig verwendete Abfragen

-- Index für sleep.end_time (wird häufig für Filterung verwendet)
CREATE INDEX IF NOT EXISTS idx_sleep_end_time ON sleep(end_time);

-- Index für sleep.type + end_time (für Nachtschlaf-Abfragen)
CREATE INDEX IF NOT EXISTS idx_sleep_type_end_time ON sleep(type, end_time);

-- Index für night_waking.start_time und end_time
CREATE INDEX IF NOT EXISTS idx_night_waking_end_time ON night_waking(end_time);

-- Composite Index für häufige Abfragen: type + start_time + end_time
CREATE INDEX IF NOT EXISTS idx_sleep_type_start_end ON sleep(type, start_time, end_time);

