#!/bin/bash

# Vauice Backend Start Script  
# This script starts the Django application with Socket.io support

# Set default port if not provided
PORT=${PORT:-8000}

echo "🚀 Starting Vauice Backend with Socket.io support..."
echo "📡 Real-time chat: Socket.io ENABLED"
echo "🌐 Port: $PORT"

# Debug environment variables at runtime
echo "🔍 Runtime Environment Check..."
python debug_env.py

echo "🔧 Environment: $(python -c "import os; print('Production' if os.getenv('DEBUG') == 'False' else 'Development')")"

# Start the WSGI server with Gevent for Socket.io
echo "🎯 Starting Gunicorn with Gevent for Socket.io..."
exec gunicorn backend.wsgi_socketio:application \
    --bind 0.0.0.0:$PORT \
    --worker-class gevent \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -