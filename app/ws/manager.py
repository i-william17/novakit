import asyncio
import json
import logging
from typing import Dict, List, Optional, Set

from fastapi import WebSocket
from config.config import settings  

logger = logging.getLogger("ws.manager")


class Connection:
    """Wrapper for WebSocket connection metadata."""
    def __init__(self, websocket: WebSocket, user_id: Optional[str] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.channels: Set[str] = set()


class WebSocketManager:
    """
    Manage active WebSocket connections, subscriptions (channels) and per-user mapping.
    Designed to be used in one process; for multi-process scaling use Redis pub/sub (below).
    """
    def __init__(self):
        self.active: List[Connection] = []
        self.user_map: Dict[str, List[Connection]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> Connection:
        await websocket.accept()
        conn = Connection(websocket, user_id=user_id)
        async with self.lock:
            self.active.append(conn)
            if user_id:
                self.user_map.setdefault(user_id, []).append(conn)
        logger.info("WS connected (user=%s). total=%d", user_id, len(self.active))
        return conn

    async def disconnect(self, conn: Connection):
        async with self.lock:
            try:
                self.active.remove(conn)
            except ValueError:
                pass
            if conn.user_id and conn.user_id in self.user_map:
                try:
                    self.user_map[conn.user_id].remove(conn)
                    if not self.user_map[conn.user_id]:
                        del self.user_map[conn.user_id]
                except ValueError:
                    pass
        logger.info("WS disconnected (user=%s). total=%d", conn.user_id, len(self.active))

    async def send_personal(self, conn: Connection, message: dict):
        await conn.websocket.send_text(json.dumps(message))

    async def send_to_user(self, user_id: str, message: dict):
        conns = self.user_map.get(user_id, [])
        for c in conns:
            await c.websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict, channel: Optional[str] = None):
        """
        Broadcast to either all connections, or only to those subscribed to `channel`.
        """
        text = json.dumps(message)
        to_send = []
        async with self.lock:
            if channel:
                for c in self.active:
                    if channel in c.channels:
                        to_send.append(c)
            else:
                to_send = list(self.active)

        for c in to_send:
            try:
                await c.websocket.send_text(text)
            except Exception:
                # if send fails, disconnect later (fire-and-forget)
                logger.exception("Failed sending WS message, scheduling disconnect")
                await self.disconnect(c)

    async def subscribe(self, conn: Connection, channel: str):
        conn.channels.add(channel)

    async def unsubscribe(self, conn: Connection, channel: str):
        conn.channels.discard(channel)
        
        
manager = WebSocketManager()
