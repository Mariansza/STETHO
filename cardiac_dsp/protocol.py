"""Binary PCM protocol for WebSocket audio streaming.

Simplified protocol — no sequence numbers or visualization data.
Client sends raw PCM float32 chunks, server responds with processed chunks.
"""

import numpy as np


def encode_pcm(pcm: np.ndarray) -> bytes:
    """Encode a PCM float32 array to raw bytes."""
    return pcm.astype(np.float32).tobytes()


def decode_pcm(data: bytes) -> np.ndarray:
    """Decode raw bytes to a PCM float32 array."""
    return np.frombuffer(data, dtype=np.float32).copy()
