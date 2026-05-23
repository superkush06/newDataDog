"""In-process pub/sub for WebSocket fanout.

For MVP: tracks active WS connections per brand and pushes JSON payloads.
v1.0 can swap to Supabase Realtime by publishing to a Postgres trigger.
"""
from collections import defaultdict
from typing import Any

_subscribers: dict[str, set] = defaultdict(set)


async def subscribe(brand_id: str, ws):
    _subscribers[brand_id].add(ws)


async def unsubscribe(brand_id: str, ws):
    _subscribers[brand_id].discard(ws)


async def publish(brand_id: str, payload: dict[str, Any]):
    """Fan out a message to all WS subscribers for a brand."""
    dead = []
    for ws in _subscribers.get(brand_id, []):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _subscribers[brand_id].discard(ws)
