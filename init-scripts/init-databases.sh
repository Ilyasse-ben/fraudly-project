#!/bin/bash
set -e

# Loop through the list of databases
for db in fraudly_assessment fraudly_learning fraudly_proctoring fraudly_analytics; do
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE $db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
EOSQL
done