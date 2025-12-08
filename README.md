# Authenticated WebSocket Application

A FastAPI-based WebSocket application with JWT authentication, peer-to-peer messaging, and broadcasting capabilities.

📖 **For detailed usage instructions, see [USAGE_GUIDE.md](./USAGE_GUIDE.md)**

## Features

- ✅ WebSocket connections with JWT token authentication
- ✅ Peer-to-peer messaging
- ✅ Broadcast messaging to all connected users
- ✅ Connection management and user tracking
- ✅ Docker Compose setup with Nginx reverse proxy
- ✅ SSL/TLS support via Let's Encrypt

## Architecture

- **FastAPI**: WebSocket server on port 8001
- **Nginx**: Reverse proxy with WebSocket support
- **Docker Compose**: Orchestrates all services

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and set JWT_SECRET
   ```

2. **Build and start services:**
   ```bash
   docker-compose up -d --build
   ```

3. **Generate a test token:**
   ```bash
   curl -X POST "http://localhost:8001/auth/token?username=user1&user_id=user1"
   ```

4. **Connect via WebSocket:**
   ```javascript
   const token = "your-jwt-token-here";
   const ws = new WebSocket(`wss://your-domain.com/ws/${token}`);
   
   ws.onopen = () => {
     console.log("Connected!");
   };
   
   ws.onmessage = (event) => {
     const data = JSON.parse(event.data);
     console.log("Received:", data);
   };
   
   // Send a message to a specific peer
   ws.send(JSON.stringify({
     type: "publish",
     peer_user_id: "user2",
     message: { text: "Hello peer!" }
   }));
   
   // Broadcast to all users
   ws.send(JSON.stringify({
     type: "publish",
     message: { text: "Hello everyone!" }
   }));
   ```

## API Endpoints

### REST Endpoints

- `POST /auth/token?username={username}&user_id={user_id}` - Generate JWT token
- `GET /health` - Health check
- `GET /users/connected` - List connected users

### WebSocket Endpoint

- `WS /ws/{token}` - WebSocket connection with JWT authentication

## Message Types

### Client to Server

1. **Publish to Peer:**
   ```json
   {
     "type": "publish",
     "peer_user_id": "user2",
     "message": { "text": "Hello!" }
   }
   ```

2. **Broadcast:**
   ```json
   {
     "type": "publish",
     "message": { "text": "Hello everyone!" }
   }
   ```

3. **Ping:**
   ```json
   {
     "type": "ping"
   }
   ```

### Server to Client

1. **Connection:**
   ```json
   {
     "type": "connection",
     "status": "connected",
     "user_id": "user1",
     "username": "user1",
     "connection_id": "user1_1234567890",
     "timestamp": "2024-01-01T00:00:00"
   }
   ```

2. **Published Message:**
   ```json
   {
     "type": "published",
     "from": "user1",
     "timestamp": "2024-01-01T00:00:00",
     "message": { "text": "Hello!" }
   }
   ```

3. **Publish Confirmation:**
   ```json
   {
     "type": "publish_confirmation",
     "from": "user1",
     "peer_user_id": "user2",
     "timestamp": "2024-01-01T00:00:00",
     "message": { "text": "Hello!" }
   }
   ```

4. **Pong:**
   ```json
   {
     "type": "pong",
     "timestamp": "2024-01-01T00:00:00"
   }
   ```

## Configuration

### Nginx Configuration

The nginx configuration supports:
- SSL/TLS termination
- WebSocket proxying with proper headers
- Multiple server blocks for different domains
- Static file serving

### Environment Variables

- `JWT_SECRET`: Secret key for JWT token signing (required in production)

## Development

Run without Docker:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Production Considerations

1. **Change JWT_SECRET** in production
2. **Use environment variables** for sensitive data
3. **Implement proper authentication** - replace the test token endpoint
4. **Add rate limiting** for WebSocket connections
5. **Monitor connection limits** and implement scaling
6. **Use Redis** for connection management in multi-instance deployments
7. **Add logging** and monitoring

## License

MIT

