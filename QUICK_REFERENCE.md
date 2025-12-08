# Quick Reference Card

## Start Services

```bash
# Docker Compose
docker compose up -d --build

# Or direct Python
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Get Token

```bash
curl -X POST "http://localhost:8001/auth/token?username=user1&user_id=user1"
```

## WebSocket Connection

```javascript
const token = "your-token-here";
const ws = new WebSocket(`ws://localhost:8001/ws/${token}`);
```

## Send Messages

**To Peer:**
```json
{
  "type": "publish",
  "peer_user_id": "user2",
  "message": { "text": "Hello!" }
}
```

**Broadcast:**
```json
{
  "type": "publish",
  "message": { "text": "Hello everyone!" }
}
```

**Ping:**
```json
{
  "type": "ping"
}
```

## API Endpoints

- `POST /auth/token` - Get JWT token
- `GET /health` - Health check
- `GET /users/connected` - List connected users
- `WS /ws/{token}` - WebSocket connection

## Test Client

Open `test_client.html` in your browser for a visual interface.

## Troubleshooting

**Service not running?**
```bash
docker compose ps
docker compose logs fastapi
```

**Port in use?**
```bash
lsof -i :8001
```

**Check health:**
```bash
curl http://localhost:8001/health
```

For more details, see [USAGE_GUIDE.md](./USAGE_GUIDE.md)

