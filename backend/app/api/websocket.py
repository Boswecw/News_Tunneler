"""WebSocket endpoints for real-time alerts."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.logging import logger
import json

router = APIRouter(tags=["websocket"])

# Store active connections
active_connections: list[WebSocket] = []


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert streaming.
    
    Broadcasts new high-score articles to all connected clients.
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(active_connections)}")
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back or handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


async def broadcast_alert(article_data: dict) -> None:
    """
    Broadcast alert to all connected WebSocket clients.
    
    Args:
        article_data: Dictionary with article and score information
    """
    if not active_connections:
        return
    
    message = json.dumps({
        "type": "alert",
        "data": article_data,
    })
    
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            disconnected.append(connection)
    
    # Clean up disconnected clients
    for connection in disconnected:
        if connection in active_connections:
            active_connections.remove(connection)

