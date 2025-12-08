# WebSocket Authentication - Complete Usage Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Setup Instructions](#setup-instructions)
3. [Getting Started](#getting-started)
4. [Authentication](#authentication)
5. [WebSocket Connection](#websocket-connection)
6. [Sending Messages](#sending-messages)
7. [Code Examples](#code-examples)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Start the Services

```bash
# Using Docker Compose (Recommended)
docker compose up -d --build

# Or use the startup script
./start.sh

# Or run directly (for development)
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Get a Token

```bash
curl -X POST "http://localhost:8001/auth/token?username=user1&user_id=user1"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "user1",
  "username": "user1"
}
```

### 3. Connect via WebSocket

```javascript
const token = "your-token-here";
const ws = new WebSocket(`ws://localhost:8001/ws/${token}`);
```

---

## Setup Instructions

### Prerequisites

- Docker and Docker Compose (for containerized deployment)
- OR Python 3.11+ (for direct running)
- SSL certificates (for production with nginx)

### Environment Variables

Create a `.env` file (optional):

```bash
JWT_SECRET=your-secret-key-change-in-production
```

### Docker Setup

1. **Build and start services:**
   ```bash
   docker compose up -d --build
   ```

2. **Check service status:**
   ```bash
   docker compose ps
   ```

3. **View logs:**
   ```bash
   docker compose logs -f fastapi
   ```

4. **Stop services:**
   ```bash
   docker compose down
   ```

### Direct Python Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

---

## Getting Started

### Using the Test Client (HTML)

1. Open `test_client.html` in your web browser
2. Set the API URL (default: `http://localhost:8001`)
3. Enter a username (e.g., `user1`)
4. Click "Get Token"
5. Click "Connect" to establish WebSocket connection
6. Send messages using the form

### Using cURL

**Get a token:**
```bash
curl -X POST "http://localhost:8001/auth/token?username=alice&user_id=alice"
```

**Health check:**
```bash
curl http://localhost:8001/health
```

**List connected users:**
```bash
curl http://localhost:8001/users/connected
```

---

## Authentication

### Getting a JWT Token

**Endpoint:** `POST /auth/token`

**Parameters:**
- `username` (required): Username for the token
- `user_id` (optional): User ID (defaults to username)

**Example:**
```bash
curl -X POST "http://localhost:8001/auth/token?username=alice&user_id=alice123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "alice123",
  "username": "alice"
}
```

### Token Expiration

Tokens expire after 24 hours by default. You'll need to generate a new token after expiration.

---

## WebSocket Connection

### Connection URL Format

```
ws://host:port/ws/{token}
wss://host:port/ws/{token}  (for HTTPS)
```

### Examples

**Local development:**
```
ws://localhost:8001/ws/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Production (with nginx):**
```
wss://websockets.encryptedbar.com/ws/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Connection Flow

1. **Connect:** WebSocket connection is established
2. **Authenticate:** Token is validated automatically
3. **Welcome Message:** Server sends connection confirmation
4. **Ready:** You can now send and receive messages

### Welcome Message

When you connect, you'll receive:
```json
{
  "type": "connection",
  "status": "connected",
  "user_id": "user1",
  "username": "user1",
  "connection_id": "user1_1234567890.123",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## Sending Messages

### Message Types

#### 1. Publish to Specific Peer

Send a message to a specific user:

```json
{
  "type": "publish",
  "peer_user_id": "user2",
  "message": {
    "text": "Hello user2!",
    "data": { "any": "custom data" }
  }
}
```

**Response (to sender):**
```json
{
  "type": "publish_confirmation",
  "from": "user1",
  "peer_user_id": "user2",
  "timestamp": "2024-01-01T12:00:00",
  "message": { "text": "Hello user2!" }
}
```

**Message received by peer:**
```json
{
  "type": "published",
  "from": "user1",
  "timestamp": "2024-01-01T12:00:00",
  "message": { "text": "Hello user2!" }
}
```

#### 2. Broadcast to All Users

Send a message to all connected users:

```json
{
  "type": "publish",
  "message": {
    "text": "Hello everyone!",
    "announcement": true
  }
}
```

**Response (to sender):**
```json
{
  "type": "broadcast_confirmation",
  "from": "user1",
  "timestamp": "2024-01-01T12:00:00",
  "message": { "text": "Hello everyone!" }
}
```

#### 3. Ping (Keep-Alive)

Check connection status:

```json
{
  "type": "ping"
}
```

**Response:**
```json
{
  "type": "pong",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## Code Examples

### JavaScript/TypeScript

```javascript
// Get token first
async function getToken(username, userId) {
  const response = await fetch(
    `http://localhost:8001/auth/token?username=${username}&user_id=${userId}`,
    { method: 'POST' }
  );
  const data = await response.json();
  return data.access_token;
}

// Connect to WebSocket
const token = await getToken('user1', 'user1');
const ws = new WebSocket(`ws://localhost:8001/ws/${token}`);

// Connection opened
ws.onopen = () => {
  console.log('Connected!');
};

// Listen for messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  
  switch(data.type) {
    case 'connection':
      console.log('Connected as:', data.user_id);
      break;
    case 'published':
      console.log('Message from', data.from, ':', data.message);
      break;
    case 'pong':
      console.log('Pong received');
      break;
  }
};

// Send message to peer
function sendToPeer(peerUserId, message) {
  ws.send(JSON.stringify({
    type: 'publish',
    peer_user_id: peerUserId,
    message: message
  }));
}

// Broadcast message
function broadcast(message) {
  ws.send(JSON.stringify({
    type: 'publish',
    message: message
  }));
}

// Send ping
function ping() {
  ws.send(JSON.stringify({ type: 'ping' }));
}

// Close connection
ws.onclose = () => {
  console.log('Disconnected');
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### Python

```python
import asyncio
import websockets
import json
import requests

# Get token
def get_token(username, user_id=None):
    url = f"http://localhost:8001/auth/token"
    params = {"username": username}
    if user_id:
        params["user_id"] = user_id
    response = requests.post(url, params=params)
    return response.json()["access_token"]

# WebSocket connection
async def connect_and_chat():
    token = get_token("user1", "user1")
    uri = f"ws://localhost:8001/ws/{token}"
    
    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        print(f"Connected: {json.loads(welcome)}")
        
        # Send message to peer
        message = {
            "type": "publish",
            "peer_user_id": "user2",
            "message": {"text": "Hello from Python!"}
        }
        await websocket.send(json.dumps(message))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

# Run
asyncio.run(connect_and_chat())
```

### Node.js

```javascript
const WebSocket = require('ws');
const axios = require('axios');

// Get token
async function getToken(username, userId) {
  const response = await axios.post(
    'http://localhost:8001/auth/token',
    null,
    { params: { username, user_id: userId } }
  );
  return response.data.access_token;
}

// Connect
async function connect() {
  const token = await getToken('user1', 'user1');
  const ws = new WebSocket(`ws://localhost:8001/ws/${token}`);
  
  ws.on('open', () => {
    console.log('Connected!');
    
    // Send message to peer
    ws.send(JSON.stringify({
      type: 'publish',
      peer_user_id: 'user2',
      message: { text: 'Hello from Node.js!' }
    }));
  });
  
  ws.on('message', (data) => {
    const message = JSON.parse(data.toString());
    console.log('Received:', message);
  });
  
  ws.on('error', (error) => {
    console.error('Error:', error);
  });
  
  ws.on('close', () => {
    console.log('Disconnected');
  });
}

connect();
```

### cURL (WebSocket testing with wscat)

```bash
# Install wscat: npm install -g wscat

# Get token first
TOKEN=$(curl -s -X POST "http://localhost:8001/auth/token?username=user1&user_id=user1" | jq -r '.access_token')

# Connect
wscat -c "ws://localhost:8001/ws/$TOKEN"

# Then type messages:
# {"type":"publish","peer_user_id":"user2","message":{"text":"Hello"}}
# {"type":"ping"}
```

---

## API Reference

### REST Endpoints

#### `POST /auth/token`
Generate JWT token for WebSocket authentication.

**Query Parameters:**
- `username` (required): Username
- `user_id` (optional): User ID

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user_id": "string",
  "username": "string"
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "active_connections": 5,
  "active_users": 3
}
```

#### `GET /users/connected`
List all connected users.

**Response:**
```json
{
  "users": ["user1", "user2", "user3"],
  "total_connections": 5
}
```

### WebSocket Endpoint

#### `WS /ws/{token}`
WebSocket connection with JWT authentication.

**Path Parameter:**
- `token`: JWT token from `/auth/token`

**Message Format (Client → Server):**
```json
{
  "type": "publish" | "ping",
  "peer_user_id": "string" (optional, for publish),
  "message": {} (required for publish)
}
```

**Message Format (Server → Client):**
- Connection: `{"type": "connection", ...}`
- Published: `{"type": "published", "from": "...", "message": {...}}`
- Confirmation: `{"type": "publish_confirmation", ...}`
- Pong: `{"type": "pong", "timestamp": "..."}`
- Error: `{"type": "error", "message": "..."}`

---

## Troubleshooting

### "Failed to fetch" Error

**Problem:** Cannot connect to the API.

**Solutions:**
1. Check if the service is running:
   ```bash
   docker compose ps
   # or
   curl http://localhost:8001/health
   ```

2. Start the service:
   ```bash
   docker compose up -d
   ```

3. Check firewall/port access:
   ```bash
   netstat -tuln | grep 8001
   ```

### "Invalid authentication credentials" Error

**Problem:** Token is invalid or expired.

**Solutions:**
1. Generate a new token
2. Check token expiration (tokens expire after 24 hours)
3. Verify JWT_SECRET matches

### WebSocket Connection Fails

**Problem:** Cannot establish WebSocket connection.

**Solutions:**
1. Verify token is valid:
   ```bash
   curl -X POST "http://localhost:8001/auth/token?username=test&user_id=test"
   ```

2. Check nginx configuration (if using nginx):
   - Ensure WebSocket headers are set
   - Verify proxy_pass points to correct port

3. Check browser console for CORS errors

4. For production (HTTPS), use `wss://` instead of `ws://`

### Peer Not Receiving Messages

**Problem:** Messages sent to peer are not received.

**Solutions:**
1. Verify peer is connected:
   ```bash
   curl http://localhost:8001/users/connected
   ```

2. Check peer_user_id matches exactly (case-sensitive)

3. Verify peer's WebSocket connection is active

### CORS Errors

**Problem:** Browser blocks requests due to CORS.

**Solutions:**
1. CORS is already configured to allow all origins (`allow_origins=["*"]`)
2. If still having issues, check browser console
3. For production, configure specific origins in `app/main.py`

### Service Won't Start

**Problem:** Docker container fails to start.

**Solutions:**
1. Check logs:
   ```bash
   docker compose logs fastapi
   ```

2. Verify port 8001 is not in use:
   ```bash
   lsof -i :8001
   ```

3. Rebuild containers:
   ```bash
   docker compose down
   docker compose up -d --build
   ```

### SSL Certificate Issues (Production)

**Problem:** SSL errors with nginx.

**Solutions:**
1. Verify certificates exist:
   ```bash
   ls -la /etc/letsencrypt/live/websockets.encryptedbar.com/
   ```

2. Update nginx.conf with correct certificate paths

3. Restart nginx:
   ```bash
   docker compose restart nginx
   ```

---

## Production Deployment

### Environment Variables

Set in `.env` or environment:
```bash
JWT_SECRET=your-very-secure-secret-key-here
```

### Nginx Configuration

1. Uncomment nginx service in `docker-compose.yml`
2. Ensure SSL certificates are mounted
3. Update `nginx.conf` with your domain
4. Restart services

### Security Considerations

1. **Change JWT_SECRET** - Use a strong, random secret
2. **Token Expiration** - Adjust in `app/main.py` if needed
3. **Rate Limiting** - Add rate limiting for production
4. **CORS** - Restrict origins in production
5. **Authentication** - Replace test token endpoint with real auth
6. **Monitoring** - Add logging and monitoring
7. **Scaling** - Use Redis for connection management in multi-instance deployments

---

## Support

For issues or questions:
1. Check logs: `docker compose logs -f fastapi`
2. Test endpoints: `curl http://localhost:8001/health`
3. Review this guide's troubleshooting section

---

## License

MIT

