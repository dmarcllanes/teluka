-- ─────────────────────────────────────────────────────────────────────────────
-- Run this once in the Supabase SQL editor (Dashboard → SQL Editor → New query)
-- ─────────────────────────────────────────────────────────────────────────────

-- Users table — created automatically on first OTP verification
-- No separate sign-up flow needed; get_or_create_user() handles both cases.
CREATE TABLE IF NOT EXISTS users (
    id                 uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    phone              text        NOT NULL UNIQUE,
    gcash_verified     boolean     NOT NULL DEFAULT false,
    maya_verified      boolean     NOT NULL DEFAULT false,
    trust_score        float       NOT NULL DEFAULT 50.0,
    trust_level        text        NOT NULL DEFAULT 'new',
    kyc_status         text        NOT NULL DEFAULT 'unverified',
    total_transactions int         NOT NULL DEFAULT 0,
    scam_reports       int         NOT NULL DEFAULT 0,
    created_at         timestamptz NOT NULL DEFAULT now()
);

-- ── RLS ───────────────────────────────────────────────────────────────────────
-- Only the server (service_role key) can read/write users.
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "no_client_access" ON users
    AS RESTRICTIVE
    FOR ALL
    TO anon, authenticated
    USING (false);
