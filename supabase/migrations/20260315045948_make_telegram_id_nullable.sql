-- Migration: make_telegram_id_nullable
-- Created at: 20260315045948

ALTER TABLE users ALTER COLUMN telegram_id DROP NOT NULL;
ALTER TABLE users ALTER COLUMN telegram_id SET DEFAULT NULL;
