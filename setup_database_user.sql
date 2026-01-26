-- Setup database user for VIMS
-- Run this with: docker exec vims-db psql -U postgres -f /tmp/setup_database_user.sql

-- Create user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'vims_user') THEN
        CREATE USER vims_user WITH PASSWORD 'vims_password';
        RAISE NOTICE 'User vims_user created';
    ELSE
        RAISE NOTICE 'User vims_user already exists';
    END IF;
END
$$;

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE vims_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vims_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE vims_db TO vims_user;

-- Connect to vims_db and grant schema privileges
\c vims_db

-- Grant privileges on all tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO vims_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO vims_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO vims_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO vims_user;

