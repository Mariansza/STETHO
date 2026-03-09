"""FastAPI backend for real-time stethoscope audio processing."""

import logging

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.audio.devices import list_devices, get_device_info
from backend.websocket.handler import AudioWebSocketHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stetho", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/devices")
async def devices() -> list[dict]:
    """List available audio input devices."""
    return list_devices()


@app.get("/api/devices/{device_id}")
async def device_info(device_id: int) -> dict:
    info = get_device_info(device_id)
    if info is None:
        return {"error": "Device not found"}
    return info


@app.websocket("/ws/audio")
async def ws_audio(ws: WebSocket) -> None:
    """WebSocket endpoint for real-time audio streaming."""
    handler = AudioWebSocketHandler()
    await handler.handle(ws)
