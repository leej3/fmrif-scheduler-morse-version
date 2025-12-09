-- Remove reset_tokens table (no longer needed with JWT-only authentication)
-- Phase 2: Backend OAuth implementation uses JWT tokens instead of server-side token storage

DROP TABLE IF EXISTS reset_tokens;

-- site_sessions table is kept for Flask session support in case server-rendered pages need it
