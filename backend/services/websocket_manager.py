"""
WebSocket connection management.

Manages active WebSocket connections per user for real-time audio analysis.
"""

from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections per user."""

    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}  # user_id -> websocket

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"🔌 WebSocket connected for user {user_id}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"🔌 WebSocket disconnected for user {user_id}")

    async def send_json(self, user_id: int, data: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(data)
