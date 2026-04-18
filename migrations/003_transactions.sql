-- ─────────────────────────────────────────────────────────────────────────────
-- Run this once in the Supabase SQL editor (Dashboard → SQL Editor → New query)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS transactions (
    id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    buyer_id             uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seller_id            uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_description     text        NOT NULL,
    amount_centavos      int         NOT NULL CHECK (amount_centavos > 0),
    status               text        NOT NULL DEFAULT 'pending',
    payment_intent_id    text,
    evidence_photo_urls  text[]      NOT NULL DEFAULT '{}',
    unboxing_video_url   text,
    delivery_tracking_id text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    expires_at           timestamptz
);

CREATE INDEX IF NOT EXISTS idx_tx_buyer   ON transactions (buyer_id);
CREATE INDEX IF NOT EXISTS idx_tx_seller  ON transactions (seller_id);
CREATE INDEX IF NOT EXISTS idx_tx_status  ON transactions (status);
CREATE INDEX IF NOT EXISTS idx_tx_created ON transactions (created_at DESC);

-- ── RLS ───────────────────────────────────────────────────────────────────────
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "no_client_access" ON transactions
    AS RESTRICTIVE
    FOR ALL
    TO anon, authenticated
    USING (false);
