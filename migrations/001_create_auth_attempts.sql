-- 001_create_auth_attempts.sql
-- Tracks every voice PIN/auth attempt for audit, lockout analysis, and incident response.
-- Run this in your Supabase SQL Editor before enabling remote auth logging.

CREATE TABLE IF NOT EXISTS auth_attempts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    caller_name text,
    pin_length int,
    success boolean NOT NULL,
    reason text,
    source text DEFAULT 'vapi_voice',
    client_ip text,
    user_agent text,
    assistant_id text,
    created_at timestamptz DEFAULT now()
);

-- Indexes for the audit queries used by the admin dashboard and alerting.
CREATE INDEX IF NOT EXISTS idx_auth_attempts_created_at
    ON auth_attempts (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_auth_attempts_caller_name
    ON auth_attempts (caller_name);

CREATE INDEX IF NOT EXISTS idx_auth_attempts_success
    ON auth_attempts (success, created_at DESC);

-- Optional: expose a secure view for non-admin callers (no IP/UA).
CREATE OR REPLACE VIEW auth_attempts_public AS
SELECT
    id,
    caller_name,
    pin_length,
    success,
    reason,
    source,
    assistant_id,
    created_at
FROM auth_attempts;

-- Optional RLS policy: restrict direct table access to service_role.
-- Enable RLS if you want user-facing apps to read only the public view.
-- ALTER TABLE auth_attempts ENABLE ROW LEVEL SECURITY;
