
-- Migration: Add auth fields to users table
-- Target: 20260315043926_add_auth_fields_to_users

ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);
