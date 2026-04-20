-- 008_missing_columns.sql
-- Adds columns that the app writes/reads but were never in a prior migration.
-- Safe to run multiple times (all use IF NOT EXISTS / IF NOT EXISTS equivalents).

-- ── users: wallet pending numbers ─────────────────────────────────────────────
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS gcash_pending_number text,
    ADD COLUMN IF NOT EXISTS maya_pending_number  text;

-- ── transactions: protection plan, fee, audit timestamp ───────────────────────
ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS protection_plan       text        NOT NULL DEFAULT 'basic',
    ADD COLUMN IF NOT EXISTS platform_fee_centavos int         NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS updated_at            timestamptz;

ANALYZE users;
ANALYZE transactions;
