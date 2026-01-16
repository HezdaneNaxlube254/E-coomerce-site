#!/usr/bin/env bash
# Build script for Render

echo "=== Starting build process ==="

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations (this will be done in start command)
echo "Build completed successfully!"
