-- W1 database bootstrap only. No application tables or seed data yet.
-- BE2 adds versioned migrations when the Jira schema decision is approved.
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Tao database rieng cho SonarQube tren cung PostgreSQL server (tranh canh bao Embedded H2)
SELECT 'CREATE DATABASE sonarqube'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sonarqube')\gexec
