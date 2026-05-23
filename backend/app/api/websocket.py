"""WebSocket routes."""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

try:
    from app.core.realtime import subscribe, unsubscribe
except ImportError:
    subscribe = None
    unsubscribe = None


router = APIRouter()


@router.websocket("/ws/feed/{brand_id}")
async def feed_socket(websocket: WebSocket, brand_id: str) -> None:
    await websocket.accept()
    if subscribe is None:
        await websocket.send_json(
            {
                "type": "status",
                "brand_id": brand_id,
                "status": "connected",
                "mode": "placeholder",
                "reason": "missing_realtime_backend",
            }
        )
    else:
        await subscribe(brand_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if unsubscribe is not None:
            await unsubscribe(brand_id, websocket)
