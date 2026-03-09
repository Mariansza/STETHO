"""WebSocket protocol: binary audio frames and JSON control messages."""

import json
import struct

import numpy as np


def encode_audio_frame(seq: int, pcm: np.ndarray) -> bytes:
    """Encode a PCM audio frame as binary:
    [4 bytes seq uint32 LE] + [N × 4 bytes float32 LE]
    """
    header = struct.pack("<I", seq & 0xFFFFFFFF)
    return header + pcm.astype(np.float32).tobytes()


def encode_viz_message(data: dict) -> str:
    """Encode visualization data as JSON string."""
    return json.dumps(data)


def decode_client_message(raw: str) -> dict:
    """Decode a JSON control message from the client."""
    return json.loads(raw)
