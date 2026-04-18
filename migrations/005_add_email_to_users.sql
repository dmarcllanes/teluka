-- ─────────────────────────────────────────────────────────────────────────────
-- 005_add_email_to_users.sql
-- Run once in Supabase SQL Editor (Dashboard → SQL Editor → New query)
-- ─────────────────────────────────────────────────────────────────────────────

-- Add email column — unique, required for new users
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email text;

-- Unique index so two accounts can't share the same email
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
    ON users (email)
    WHERE email IS NOT NULL;

-- Fast lookup by email for login
CREATE INDEX IF NOT EXISTS idx_users_email_lower
    ON users (lower(email))
    WHERE email IS NOT NULL;
