-- 009_profile_photos.sql
-- Adds profile picture and real-time trust photo columns to users.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS avatar_url           text,
    ADD COLUMN IF NOT EXISTS trust_photo_url      text,
    ADD COLUMN IF NOT EXISTS trust_photo_taken_at timestamptz;

ANALYZE users;

-- Supabase Storage buckets to create manually in the dashboard:
--   1. "avatars"      — public read, 2 MB limit, MIME: image/jpeg
--   2. "trust-photos" — public read, 5 MB limit, MIME: image/jpeg
