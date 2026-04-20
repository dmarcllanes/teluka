-- 011_location_on_events.sql
-- Records the actor's GPS coordinates at the moment each deal action is taken.
-- Coordinates are optional (null when user denies location permission).

ALTER TABLE transaction_events
  ADD COLUMN IF NOT EXISTS actor_lat double precision,
  ADD COLUMN IF NOT EXISTS actor_lon double precision;

ANALYZE transaction_events;
