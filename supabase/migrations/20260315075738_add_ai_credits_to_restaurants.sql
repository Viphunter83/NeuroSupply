-- Add AI credits to restaurants
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS ai_credits INTEGER DEFAULT 1000;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS total_ai_usage INTEGER DEFAULT 0;
