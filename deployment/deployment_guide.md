# Vauice Backend Deployment Guide

## ASGI Deployment for WebSocket Support

Your Django backend uses **Django Channels** for real-time WebSocket connections. This requires an **ASGI server** (not WSGI) for proper WebSocket support.

## Render.com Deployment

### Method 1: Using render.yaml (Recommended)

1. Use the provided `render.yaml` file in your repository
2. Connect your GitHub repo to Render
3. Render will automatically use the configuration

### Method 2: Manual Configuration

**Service Settings:**
- **Environment**: Python 3.12
- **Build Command**: `./build.sh`
- **Start Command**: `daphne backend.asgi:application --port $PORT --bind 0.0.0.0 --verbosity 2`
- **Health Check Path**: `/ping/`

### Required Environment Variables

```bash
# Essential
SECRET_KEY=your-secret-key
DEBUG=False
DB_CONN_URL=your-database-url
REDIS_URL=your-redis-url

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# SendGrid (optional)
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@vauice.com
SENDGRID_FROM_NAME=Vauice Team
```

## WebSocket Endpoints

After successful deployment, your WebSocket endpoints will be available at:

- **Chat**: `wss://your-app.onrender.com/ws/chat/{room_id}/?token={jwt_token}`
- **Presence**: `wss://your-app.onrender.com/ws/presence/?token={jwt_token}`

## Local Development

### Start with ASGI locally:
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start with ASGI server
daphne backend.asgi:application --port 8000 --bind 127.0.0.1

# OR use the start script
chmod +x start.sh
./start.sh
```

### Test WebSocket connections:
```bash
# Install wscat for testing
npm install -g wscat

# Test presence connection
wscat -c "ws://localhost:8000/ws/presence/?token=YOUR_JWT_TOKEN"

# Test chat connection (replace ROOM_ID)
wscat -c "ws://localhost:8000/ws/chat/ROOM_ID/?token=YOUR_JWT_TOKEN"
```

## Production Checklist

- [ ] Deploy with ASGI server (daphne/uvicorn)
- [ ] Set `DEBUG=False`
- [ ] Configure Redis for channel layers
- [ ] Set up database (PostgreSQL recommended)
- [ ] Configure Cloudinary for file storage
- [ ] Set up proper domain in `ALLOWED_HOSTS`
- [ ] Enable HTTPS/WSS in production
- [ ] Set up monitoring and logging
- [ ] Configure cleanup cron jobs

## Troubleshooting

### WebSocket 404 Errors
- **Cause**: Running with WSGI instead of ASGI
- **Solution**: Ensure start command uses `daphne` or `uvicorn`

### WebSocket Connection Refused
- **Cause**: Missing Redis or channel layer configuration
- **Solution**: Verify `REDIS_URL` environment variable

### Rate Limiting Issues
- **Cause**: Redis cache not configured
- **Solution**: Ensure Redis is available and `CACHES` is configured

## Performance Optimization

### For High Traffic:
1. Use Redis cluster for channel layers
2. Implement horizontal scaling with multiple ASGI workers
3. Use CDN for static files
4. Enable database connection pooling
5. Monitor WebSocket connection limits

### Start Command for Production:
```bash
daphne backend.asgi:application \
  --port $PORT \
  --bind 0.0.0.0 \
  --verbosity 1 \
  --access-log \
  --proxy-headers
```

## Monitoring

Monitor these metrics:
- WebSocket connection count
- Redis memory usage
- Database connection pool
- Message delivery rates
- Chat room activity