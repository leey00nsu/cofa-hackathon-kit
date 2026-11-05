-- Optional integration-test database. No application or business tables.
-- Official postgres init scripts run only when initializing a NEW empty volume.
-- Existing volumes are unchanged. psql connects as POSTGRES_USER (the DB owner).
SELECT format('CREATE DATABASE cofa_test OWNER %I', current_user)
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cofa_test')
\gexec
