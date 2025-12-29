#!/bin/bash
echo "=== FORCING CLEAN BUILD ==="

# Clear any Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Install requirements
echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "=== BUILD COMPLETE ==="
