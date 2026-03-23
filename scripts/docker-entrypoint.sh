#!/bin/sh
set -e

# Create required runtime directories
mkdir -p /data/reports /data/documents /app/reports /app/manifests

# Ensure config exists (use example if user hasn't configured one)
if [ ! -f /app/config/jurisdiction.json ]; then
    echo "[INFO] No jurisdiction.json found — using example config."
    echo "[INFO] Run: docker exec -it <container> python scripts/setup_jurisdiction.py"
    cp /app/config/jurisdiction.example.json /app/config/jurisdiction.json
fi

echo "[OK] O.D.I.A. starting on http://localhost:8080"
exec supervisord -c /etc/supervisord.conf
