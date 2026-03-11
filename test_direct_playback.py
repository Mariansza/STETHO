"""Direct capture → DSP → playback test (no WebSocket, no browser).

If this crackles: the DSP is the problem.
If this is clean: the WebSocket/AudioWorklet streaming is the problem.

Press Enter to stop.
"""
import sounddevice as sd
import numpy as np
from backend.dsp.pipeline import DSPPipeline
from backend.config import CHUNK_SIZE

DEVICE_IN = 1  # ri-sonic PCP-USB-A (MME)

dev_info = sd.query_devices(DEVICE_IN)
sr = int(dev_info["default_samplerate"])
print(f"Device: {dev_info['name']}")
print(f"Sample rate: {sr} Hz")
print(f"Chunk size: {CHUNK_SIZE}")

pipeline = DSPPipeline(mode="cardiac", sample_rate=sr)
print(f"Mode: cardiac (20-250 Hz)")
print()
print("Lecture directe avec DSP... Appuie sur Entree pour arreter.")
print("(Pas de WebSocket, pas de navigateur)")


def callback(indata, outdata, frames, time_info, status):
    if status:
        print(f"  [status] {status}")
    chunk = indata[:, 0].copy()
    processed = pipeline.process(chunk)
    outdata[:, 0] = processed


with sd.Stream(
    samplerate=sr,
    blocksize=CHUNK_SIZE,
    device=(DEVICE_IN, None),
    channels=1,
    dtype="float32",
    callback=callback,
):
    input()

print("Arrete.")
