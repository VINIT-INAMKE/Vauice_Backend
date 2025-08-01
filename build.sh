#!/bin/bash

echo "🚀 Starting Vauice Backend Build Process..."

echo "📦 Installing Dependencies..."
pip install -r requirements.txt 

echo "🗂️ Collecting Static Files..."
python manage.py collectstatic --no-input 

echo "🔄 Making migrations..."
python manage.py makemigrations

echo "⬆️ Migrating Database..." 
python manage.py migrate

echo "🧹 Running cleanup for orphaned data..."
python manage.py cleanup_chat --days=30 || echo "⚠️ Cleanup failed, continuing..."

echo "✅ Build Complete! Ready for ASGI deployment with WebSocket support."