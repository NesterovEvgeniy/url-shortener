#!/bin/bash
set -e

# Ждем, пока PostgreSQL будет готов
echo "Waiting for PostgreSQL..."
sleep 5

# Применяем миграции
echo "Applying migrations..."
alembic upgrade head

# Запускаем основное приложение
echo "Starting application..."
exec "$@"