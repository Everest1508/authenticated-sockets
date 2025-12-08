from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
import json
from typing import Dict, List, Optional
from datetime import datetime
import os
from pydantic import BaseModel

app = FastAPI(title="Authenticated WebSocket API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# JWT Secret (in production, use environment variable)
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}  # user_id -> [connection_ids]
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
    
    def disconnect(self, connection_id: str, user_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if user_id in self.user_connections and connection_id in self.user_connections[user_id]:
            self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    async def send_personal_message(self, message: str, connection_id: str):
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_text(message)
    
    async def send_to_user(self, message: str, user_id: str):
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                await self.send_personal_message(message, connection_id)
    
    async def broadcast(self, message: str, exclude_connection_id: Optional[str] = None):
        for connection_id, connection in self.active_connections.items():
            if connection_id != exclude_connection_id:
                await connection.send_text(message)
    
    async def send_to_peer(self, message: str, peer_user_id: str, sender_user_id: str):
        """Send message to a specific peer user"""
        if peer_user_id in self.user_connections:
            for connection_id in self.user_connections[peer_user_id]:
                await self.send_personal_message(message, connection_id)

manager = ConnectionManager()

# Models
class TokenData(BaseModel):
    user_id: str
    username: str

class PublishMessage(BaseModel):
    peer_user_id: Optional[str] = None  # If None, broadcast to all
    message: dict

# Authentication functions
def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username", "unknown")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return TokenData(user_id=user_id, username=username)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    return verify_token(credentials.credentials)

# WebSocket endpoint with authentication
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint with token-based authentication.
    Connect using: ws://host/ws/{token}
    """
    try:
        # Verify token
        token_data = verify_token(token)
        connection_id = f"{token_data.user_id}_{datetime.now().timestamp()}"
        
        await manager.connect(websocket, connection_id, token_data.user_id)
        
        # Send welcome message
        welcome_msg = {
            "type": "connection",
            "status": "connected",
            "user_id": token_data.user_id,
            "username": token_data.username,
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_msg))
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")
                
                if message_type == "publish":
                    # Publish message to peer or broadcast
                    peer_user_id = message_data.get("peer_user_id")
                    message_content = message_data.get("message", {})
                    
                    response = {
                        "type": "published",
                        "from": token_data.user_id,
                        "timestamp": datetime.now().isoformat(),
                        "message": message_content
                    }
                    
                    if peer_user_id:
                        # Send to specific peer
                        await manager.send_to_peer(
                            json.dumps(response),
                            peer_user_id,
                            token_data.user_id
                        )
                        # Also send confirmation to sender
                        await websocket.send_text(json.dumps({
                            **response,
                            "type": "publish_confirmation",
                            "peer_user_id": peer_user_id
                        }))
                    else:
                        # Broadcast to all except sender
                        await manager.broadcast(
                            json.dumps(response),
                            exclude_connection_id=connection_id
                        )
                        await websocket.send_text(json.dumps({
                            **response,
                            "type": "broadcast_confirmation"
                        }))
                
                elif message_type == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                else:
                    # Echo back unknown message types
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
    except WebSocketDisconnect:
        manager.disconnect(connection_id, token_data.user_id)
    except Exception as e:
        manager.disconnect(connection_id, token_data.user_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))

# REST endpoint to generate test token (for development)
@app.post("/auth/token")
async def create_token(username: str, user_id: Optional[str] = None):
    """
    Generate a test JWT token for WebSocket authentication.
    In production, this should be handled by your authentication service.
    """
    if not user_id:
        user_id = username
    
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.now().timestamp() + 86400  # 24 hours
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "username": username
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "active_users": len(manager.user_connections)
    }

# Get connected users
@app.get("/users/connected")
async def get_connected_users():
    return {
        "users": list(manager.user_connections.keys()),
        "total_connections": len(manager.active_connections)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

