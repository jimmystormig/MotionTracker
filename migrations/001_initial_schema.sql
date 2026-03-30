-- Migration: 001_initial_schema.sql
-- MotionTracker GPS data storage schema

CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(255) UNIQUE NOT NULL,
    friendly_name VARCHAR(255),
    activity_entity_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_entity_id ON devices(entity_id);

CREATE TABLE IF NOT EXISTS locations (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    accuracy DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    speed DOUBLE PRECISION,
    battery SMALLINT,
    activity_state VARCHAR(50),
    movement_type VARCHAR(20) NOT NULL DEFAULT 'unknown'
        CHECK (movement_type IN ('stationary', 'walking', 'running', 'cycling', 'driving', 'unknown')),
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_locations_device_time
    ON locations(device_id, recorded_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_locations_device_recorded_unique
    ON locations(device_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_locations_recorded_at
    ON locations(recorded_at DESC);
