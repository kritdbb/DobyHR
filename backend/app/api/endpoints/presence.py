import logging
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import jwt, JWTError
from app.core.config import settings

logger = logging.getLogger("presence")

router = APIRouter(tags=["presence"])

# ── In-memory presence store ──────────────────────────
# user_id → WebSocket
_online: Dict[int, WebSocket] = {}


def get_online_user_ids() -> list:
    """Return sorted list of currently online user IDs."""
    return sorted(_online.keys())


@router.get("/api/presence/online")
def get_online_users():
    """REST endpoint: return list of online user IDs (for initial page load)."""
    return {"online": get_online_user_ids()}


async def _broadcast_online():
    """Notify all connected clients of the current online set."""
    import json
    msg = json.dumps({"type": "online", "user_ids": get_online_user_ids()})
    dead = []
    for uid, ws in _online.items():
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(uid)
    for uid in dead:
        _online.pop(uid, None)


def _extract_user_id(token: str) -> int | None:
    """Decode JWT and return user ID (sub claim), or None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (JWTError, ValueError):
        return None


@router.websocket("/ws/presence")
async def presence_ws(websocket: WebSocket, token: str = Query(...)):
    """WebSocket for real-time presence tracking."""
    user_id = _extract_user_id(token)
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    # Close previous connection for same user (e.g. tab refresh)
    old = _online.pop(user_id, None)
    if old:
        try:
            await old.close(code=4002, reason="Replaced by new connection")
        except Exception:
            pass

    _online[user_id] = websocket
    logger.info(f"👤 User {user_id} online  ({len(_online)} total)")
    await _broadcast_online()

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if _online.get(user_id) is websocket:
            _online.pop(user_id, None)
        logger.info(f"👤 User {user_id} offline ({len(_online)} total)")
        await _broadcast_online()
