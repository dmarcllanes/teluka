-- 012_auth_hardening2.sql
-- Auth audit log, IP tracking on OTP requests, last-login tracking on users.

-- Track which IP requested each OTP (for audit + future geo-binding)
ALTER TABLE otp_requests
  ADD COLUMN IF NOT EXISTS requester_ip text;

-- Track last login IP per user (used for suspicious-login alerts)
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS last_login_ip text;

-- Full auth audit log: every OTP request, success, failure, lockout, login, logout
CREATE TABLE IF NOT EXISTS auth_events (
  id          uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  event_type  text        NOT NULL,  -- otp_request | otp_success | otp_fail | login | logout | lockout | pin_fail
  user_id     text,
  identifier  text,                  -- masked email or last-4 of phone
  ip          text,
  success     boolean     NOT NULL DEFAULT false,
  created_at  timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_events_user ON auth_events (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_auth_events_ip   ON auth_events (ip,      created_at DESC);

ALTER TABLE auth_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "no_client_access" ON auth_events
  AS RESTRICTIVE FOR ALL TO anon, authenticated USING (false);

ANALYZE otp_requests;
ANALYZE users;
