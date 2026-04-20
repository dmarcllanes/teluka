-- 010_push_subscriptions.sql
-- Stores Web Push subscriptions (one per browser per user).

CREATE TABLE IF NOT EXISTS push_subscriptions (
  id           uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      text        NOT NULL,
  endpoint     text        NOT NULL,
  subscription jsonb       NOT NULL,   -- full PushSubscription JSON
  created_at   timestamptz DEFAULT now(),
  UNIQUE (user_id, endpoint)
);

CREATE INDEX IF NOT EXISTS idx_push_user ON push_subscriptions (user_id);

ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "no_client_access" ON push_subscriptions
  AS RESTRICTIVE FOR ALL TO anon, authenticated USING (false);
