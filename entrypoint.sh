#!/bin/bash
set -e

INITIALIZED_FLAG="/app/.db_initialized"

if [ ! -f "$INITIALIZED_FLAG" ]; then
    echo "Primer inicio detectado. Corriendo migraciones y seed..."

    alembic downgrade base

    alembic upgrade head

    python -m src.scripts.seed_data

    touch "$INITIALIZED_FLAG"
    echo "Inicialización completada."
else
    echo "La base de datos ya estaba inicializada. Saltando migraciones y seed."
fi

exec "$@"