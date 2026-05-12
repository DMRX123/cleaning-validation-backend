# app/api/websocket.py - FIXED
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from typing import List, Dict
import json
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                await manager.broadcast_to_session(session_id, {
                    "type": "message",
                    "session_id": session_id,
                    "data": message_data,
                    "timestamp": str(asyncio.get_event_loop().time())
                })
            except json.JSONDecodeError:
                await manager.send_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        await manager.broadcast_to_session(session_id, {
            "type": "disconnect",
            "message": "User disconnected"
        })