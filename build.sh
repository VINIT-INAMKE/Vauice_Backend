#!/bin/bash

echo "🚀 Starting Vauice Backend Build Process..."

echo "🔍 Checking Environment Variables..."
python debug_env.py

echo "📦 Installing Dependencies..."
pip install -r requirements.txt 

echo "🗂️ Collecting Static Files..."
python manage.py collectstatic --no-input 

echo "🔄 Making migrations..."
python manage.py makemigrations

echo "⬆️ Migrating Database..." 
python manage.py migrate

echo "🗂️ Creating cache table for rate limiting..."
python manage.py createcachetable

echo "🧹 Running cleanup for orphaned data..."
python manage.py cleanup_chat --days=30 || echo "⚠️ Cleanup failed, continuing..."

echo "✅ Build Complete! Ready for Socket.io deployment with sync worker."