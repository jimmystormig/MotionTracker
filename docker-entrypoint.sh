#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
python3 << 'PYEOF'
import time, os, sys
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "")
# asyncpg URL -> psycopg2 compatible
url = url.replace("postgresql+asyncpg://", "postgresql://")

parsed = urlparse(url)
host = parsed.hostname or "localhost"
port = parsed.port or 5432

import socket
for i in range(60):
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        print(f"PostgreSQL ready at {host}:{port}")
        sys.exit(0)
    except OSError:
        print(f"  waiting for {host}:{port} ({i+1}/60)...")
        time.sleep(2)

print("PostgreSQL did not become ready in time")
sys.exit(1)
PYEOF

echo "Running migrations..."
DB_URL="${DATABASE_URL}"
# Convert asyncpg URL for psql
DB_URL="${DB_URL#postgresql+asyncpg://}"
DB_URL="postgresql://${DB_URL}"

for migration_file in /app/migrations/*.sql; do
    echo "  Applying: $(basename "$migration_file")"
    psql "$DB_URL" -v ON_ERROR_STOP=0 -f "$migration_file" 2>&1 || true
done

echo "Starting MotionTracker..."
exec uvicorn src.app:app --host 0.0.0.0 --port 8000
