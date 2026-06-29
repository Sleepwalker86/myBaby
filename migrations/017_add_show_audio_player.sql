-- Migration 017: Audio-Player Sichtbarkeitseinstellung
ALTER TABLE baby_info ADD COLUMN show_audio_player INTEGER NOT NULL DEFAULT 1;
