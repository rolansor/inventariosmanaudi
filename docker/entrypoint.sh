#!/bin/sh
set -e

echo "[entrypoint] Esperando a MySQL en ${DB_HOST:-db}:${DB_PORT:-3306}..."
python - <<'PY'
import os, time, sys
import pymysql
host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "3306"))
user = os.environ.get("DB_USER", "root")
password = os.environ.get("DB_PASSWORD", "")
for intento in range(60):
    try:
        pymysql.connect(host=host, port=port, user=user, password=password, connect_timeout=3).close()
        print("[entrypoint] MySQL disponible.")
        sys.exit(0)
    except Exception as exc:
        time.sleep(2)
print("[entrypoint] MySQL no respondió a tiempo.")
sys.exit(1)
PY

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[entrypoint] Aplicando migraciones..."
    python manage.py migrate --noinput
fi

exec "$@"
