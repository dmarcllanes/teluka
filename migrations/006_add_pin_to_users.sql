-- Migration 006: add PIN hash to users
-- Run once in Supabase SQL editor

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS pin_hash text;
