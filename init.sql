
-- global extensions and audit table
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.audit_log(
  id SERIAL PRIMARY KEY,
  user_uuid TEXT,
  action TEXT,
  logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
