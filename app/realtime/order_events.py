import uuid
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder


class OrderEventManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[channel].add(websocket)

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        connections = self._connections.get(channel)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(channel, None)

    async def broadcast(self, channels: list[str], payload: dict[str, Any]) -> None:
        encoded_payload = jsonable_encoder(payload)
        seen: set[int] = set()

        for channel in channels:
            stale_connections: list[WebSocket] = []
            for websocket in list(self._connections.get(channel, set())):
                websocket_key = id(websocket)
                if websocket_key in seen:
                    continue
                seen.add(websocket_key)
                try:
                    await websocket.send_json(encoded_payload)
                except Exception:
                    stale_connections.append(websocket)

            for websocket in stale_connections:
                self.disconnect(channel, websocket)


order_event_manager = OrderEventManager()


def store_orders_channel(store_id: uuid.UUID | str) -> str:
    return f"store:{store_id}"


def catalog_order_channel(store_id: uuid.UUID | str, order_number: str) -> str:
    normalized_number = order_number.replace("#", "")
    return f"order:{store_id}:{normalized_number}"


async def publish_order_event(
    *,
    event_type: str,
    store_id: uuid.UUID | str,
    order_number: str,
    order: dict[str, Any] | None = None,
    order_id: uuid.UUID | str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "type": event_type,
        "order_number": order_number,
    }

    if order is not None:
        payload["order"] = order
        payload["order_id"] = order.get("id")
    elif order_id is not None:
        payload["order_id"] = order_id

    await order_event_manager.broadcast(
        [
            store_orders_channel(store_id),
            catalog_order_channel(store_id, order_number),
        ],
        payload,
    )
