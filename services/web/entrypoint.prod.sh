#!/bin/sh

if [ "$DATABASE" = "postgres" ]; then 
  echo "Waiting for postgres to be ready…"
  until pg_isready -h "$SQL_HOST" -p "$SQL_PORT" >/dev/null 2>&1; do
    sleep 0.1
  done
  echo "PostgreSQL is ready"
fi

exec "$@"
