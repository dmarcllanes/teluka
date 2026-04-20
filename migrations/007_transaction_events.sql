-- Activity / audit log for every transaction state change.
-- Run in Supabase SQL Editor before 001_indexes.sql.

CREATE TABLE IF NOT EXISTS transaction_events (
  id          uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  tx_id       text        NOT NULL,
  event_type  text        NOT NULL,
  actor_id    text,
  title       text        NOT NULL,
  description text        NOT NULL DEFAULT '',
  icon        text        NOT NULL DEFAULT '📋',
  created_at  timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tx_events_tx
  ON transaction_events (tx_id, created_at DESC);

ANALYZE transaction_events;
