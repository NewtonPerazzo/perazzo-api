import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.realtime.order_events import (
    catalog_order_channel,
    order_event_manager,
    store_orders_channel,
)
from app.services.order import OrderService
from app.services.store import StoreService
from app.services.user import UserService
from app.util.jwt import decode_access_token

router = APIRouter(prefix="/ws", tags=["WebSocket"])


def _get_active_user_from_token(token: str | None, db: Session):
    if not token:
        return None

    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(str(payload.get("sub")))
    except (JWTError, TypeError, ValueError):
        return None

    user = UserService(db).get_by_id(user_id)
    if not user or not user.is_active:
        return None

    return user


async def _keep_connection_open(channel: str, websocket: WebSocket) -> None:
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        order_event_manager.disconnect(channel, websocket)


@router.websocket("/orders")
async def orders_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    user = _get_active_user_from_token(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    store = StoreService(db).get_by_user_id(user.id)
    if not store:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    channel = store_orders_channel(store.id)
    await order_event_manager.connect(channel, websocket)
    await websocket.send_json({"type": "connected"})
    await _keep_connection_open(channel, websocket)


@router.websocket("/catalog/{store_slug}/orders/{order_number}")
async def catalog_order_websocket(
    websocket: WebSocket,
    store_slug: str,
    order_number: str,
    db: Session = Depends(get_db),
):
    store = StoreService(db).get_by_slug(store_slug)
    if not store or not store.has_catalog_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    order = OrderService(db).get_by_order_number(order_number, store_id=store.id)
    if not order:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    channel = catalog_order_channel(store.id, order.order_number)
    await order_event_manager.connect(channel, websocket)
    await websocket.send_json({"type": "connected"})
    await _keep_connection_open(channel, websocket)
