#!/bin/bash
set -e

# === НАСТРОЙКИ ===
CONTAINER="online-school-db-1"

# Читаем переменные из .env, если он есть
if [ -f .env ]; then
  export $(grep -E '^(DB_NAME|DB_USER|DB_PASSWORD)=' .env | xargs)
fi

DB_NAME="${DB_NAME:-your_db_name}"
DB_USER="${DB_USER:-your_db_user}"
DB_PASSWORD="${DB_PASSWORD:-your_db_password}"

if [ -z "$1" ]; then
  echo "Usage: $0 <backup_file.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"

echo "[INFO] Restoring $BACKUP_FILE to database $DB_NAME in container $CONTAINER ..."
gunzip -c "$BACKUP_FILE" | docker exec -i -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER" psql -U "$DB_USER" "$DB_NAME"
echo "[INFO] Restore complete." 