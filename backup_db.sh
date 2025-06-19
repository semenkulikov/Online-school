#!/bin/bash
set -e

# === НАСТРОЙКИ ===
BACKUP_DIR="$(pwd)/pg_backups"
CONTAINER="online-school-db-1"

# Читаем переменные из .env, если он есть
if [ -f .env ]; then
  export $(grep -E '^(DB_NAME|DB_USER|DB_PASSWORD)=' .env | xargs)
fi

DB_NAME="${DB_NAME:-your_db_name}"
DB_USER="${DB_USER:-your_db_user}"
DB_PASSWORD="${DB_PASSWORD:-your_db_password}"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
FILE="$BACKUP_DIR/backup_$DATE.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[INFO] Dumping database $DB_NAME from container $CONTAINER ..."
docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$FILE"
echo "[INFO] Backup saved to $FILE"

# Оставлять только 7 последних бэкапов
ls -1t "$BACKUP_DIR"/backup_*.sql.gz | tail -n +8 | xargs -r rm --
echo "[INFO] Old backups pruned." 


# Cron job для бэкапа БД
# 0 3 * * * /home/online-school/online-school/backup_db.sh
