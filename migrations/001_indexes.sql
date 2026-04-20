-- Run this once in Supabase SQL editor (Dashboard → SQL Editor → New query)
-- These indexes are the single highest-impact performance change.

-- Transaction lookups (dashboard, profile — every page load)
CREATE INDEX IF NOT EXISTS idx_transactions_buyer
  ON transactions(buyer_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_seller
  ON transactions(seller_id, created_at DESC);

-- User lookups
CREATE INDEX IF NOT EXISTS idx_users_phone  ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_email  ON users(email);

-- OTP cleanup queries
CREATE INDEX IF NOT EXISTS idx_otp_phone    ON otp_requests(phone);
CREATE INDEX IF NOT EXISTS idx_otp_expires  ON otp_requests(expires_at);

-- Activity feed polling (table created in 007_transaction_events.sql)
CREATE INDEX IF NOT EXISTS idx_activity_tx
  ON transaction_events(tx_id, created_at DESC);

-- Analyse after creating (updates query planner statistics)
ANALYZE transactions;
ANALYZE users;
ANALYZE otp_requests;
ANALYZE transaction_events;
