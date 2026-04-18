-- ─────────────────────────────────────────────────────────────────────────────
-- Run this once in the Supabase SQL editor (Dashboard → SQL Editor → New query)
-- ─────────────────────────────────────────────────────────────────────────────

-- OTP holding table (server-side phone verification, no Twilio/Vonage needed)
CREATE TABLE IF NOT EXISTS otp_requests (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    phone       text        NOT NULL,
    otp_hash    text        NOT NULL,      -- sha256(phone:code), never raw
    expires_at  timestamptz NOT NULL,
    attempts    int         NOT NULL DEFAULT 0,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- One active OTP per phone
CREATE UNIQUE INDEX IF NOT EXISTS idx_otp_phone ON otp_requests (phone);

-- Fast expiry clean-up queries
CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_requests (expires_at);

-- ── RLS ───────────────────────────────────────────────────────────────────────
-- The table is only accessed server-side via the service key, so we lock it
-- down completely from the client.
ALTER TABLE otp_requests ENABLE ROW LEVEL SECURITY;

-- No client access at all (server uses service_role which bypasses RLS)
CREATE POLICY "no_client_access" ON otp_requests
    AS RESTRICTIVE
    FOR ALL
    TO anon, authenticated
    USING (false);
