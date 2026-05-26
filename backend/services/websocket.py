"""
WebSocket service for real-time task status and log streaming.
"""
import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("omicsflow.websocket")


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}  # task_id -> connections
        self._global_connections: Set[WebSocket] = set()  # dashboard connections

    async def connect(self, websocket: WebSocket, task_id: str = None):
        await websocket.accept()
        if task_id:
            if task_id not in self._connections:
                self._connections[task_id] = set()
            self._connections[task_id].add(websocket)
            logger.info(f"Client connected to task {task_id}")
        else:
            self._global_connections.add(websocket)
            logger.info(f"Client connected to global channel")

    def disconnect(self, websocket: WebSocket, task_id: str = None):
        if task_id and task_id in self._connections:
            self._connections[task_id].discard(websocket)
            if not self._connections[task_id]:
                del self._connections[task_id]
        else:
            self._global_connections.discard(websocket)

    async def send_task_update(self, task_id: str, data: dict):
        """Send update to all clients watching a specific task."""
        connections = self._connections.get(task_id, set())
        message = json.dumps({"type": "task_update", "task_id": task_id, **data})
        disconnected = set()
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)
        connections -= disconnected

    async def send_global_update(self, event_type: str, data: dict):
        """Send update to all dashboard-connected clients."""
        message = json.dumps({"type": event_type, **data})
        disconnected = set()
        for ws in self._global_connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)
        self._global_connections -= disconnected

    async def broadcast_log(self, task_id: str, log_line: str):
        """Stream a log line to task watchers."""
        connections = self._connections.get(task_id, set())
        message = json.dumps({"type": "log", "task_id": task_id, "line": log_line})
        disconnected = set()
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)
        connections -= disconnected

    @property
    def active_connections(self) -> int:
        total = len(self._global_connections)
        for conns in self._connections.values():
            total += len(conns)
        return total


ws_manager = ConnectionManager()