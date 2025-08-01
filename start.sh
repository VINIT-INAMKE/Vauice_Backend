#!/bin/bash

# Vauice Backend Start Script
# This script starts the Django application with ASGI support for WebSockets

# Set default port if not provided
PORT=${PORT:-8000}

echo "🚀 Starting Vauice Backend with ASGI support..."
echo "📡 WebSocket support: ENABLED"
echo "🌐 Port: $PORT"

# Debug environment variables at runtime
echo "🔍 Runtime Environment Check..."
python debug_env.py

echo "🔧 Environment: $(python -c "import os; print('Production' if os.getenv('DEBUG') == 'False' else 'Development')")"

# Start the ASGI server
echo "🎯 Starting Daphne ASGI server..."
exec daphne backend.asgi:application \
    --port $PORT \
    --bind 0.0.0.0 \
    --verbosity 2 \
    --access-log \
    --proxy-headers