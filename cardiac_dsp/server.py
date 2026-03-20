"""Optional FastAPI microservice wrapper for CardiacFilter.

Run on the NUC as a local service:
    uvicorn cardiac_dsp.server:app --host 127.0.0.1 --port 8002

Endpoints:
    GET  /status     — filter status
    POST /toggle     — toggle on/off
    POST /gain       — set gain
    WS   /ws/process — real-time PCM audio processing
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .core import CardiacFilter
from .protocol import encode_pcm, decode_pcm

app = FastAPI(title="Cardiac DSP", version="1.0.0")
_filter = CardiacFilter()


# --- Pydantic models ---

class ToggleRequest(BaseModel):
    enabled: bool | None = None


class GainRequest(BaseModel):
    gain: float


# --- HTTP endpoints ---

@app.get("/status")
def get_status() -> dict:
    return _filter.status


@app.post("/toggle")
def toggle(body: ToggleRequest | None = None) -> dict:
    if body is not None and body.enabled is not None:
        if body.enabled:
            _filter.enable()
        else:
            _filter.disable()
    else:
        _filter.toggle()
    return {"enabled": _filter.enabled}


@app.post("/gain")
def set_gain(body: GainRequest) -> dict:
    _filter.set_gain(body.gain)
    return {"gain": body.gain}


# --- WebSocket endpoint ---

@app.websocket("/ws/process")
async def ws_process(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            data = await ws.receive_bytes()
            pcm = decode_pcm(data)
            processed = _filter.process(pcm)
            await ws.send_bytes(encode_pcm(processed))
    except WebSocketDisconnect:
        pass
