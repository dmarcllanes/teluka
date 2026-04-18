-- ─────────────────────────────────────────────────────────────────────────────
-- 004_auth_hardening.sql
-- Run this once in the Supabase SQL editor (Dashboard → SQL Editor → New query)
-- ─────────────────────────────────────────────────────────────────────────────

-- Track when users last logged in (for audit and session management)
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_login_at timestamptz;

-- ── Phone lockout table ───────────────────────────────────────────────────────
-- Records phones that are temporarily blocked from OTP verification
-- after repeated failed attempts across multiple OTP codes.
-- (Per-code brute force is already handled by otp_requests.attempts.)

CREATE TABLE IF NOT EXISTS otp_lockouts (
    phone        text        PRIMARY KEY,
    locked_until timestamptz NOT NULL,
    reason       text        NOT NULL DEFAULT 'too_many_failed_attempts',
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- ── RLS: server-only access ───────────────────────────────────────────────────
ALTER TABLE otp_lockouts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "no_client_access" ON otp_lockouts
    AS RESTRICTIVE FOR ALL TO anon, authenticated
    USING (false);

-- Automatic clean-up index — lets Supabase cron (pg_cron) sweep expired locks
CREATE INDEX IF NOT EXISTS idx_lockout_expires
    ON otp_lockouts (locked_until);

-- ── Clean-up function (optional, run via pg_cron or manually) ────────────────
-- DELETE FROM otp_lockouts WHERE locked_until < now();
-- DELETE FROM otp_requests  WHERE expires_at  < now();
