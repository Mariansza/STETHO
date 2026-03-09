"""Audio capture from USB stethoscope via sounddevice."""

import asyncio
import logging

import numpy as np
import sounddevice as sd

from backend.config import SAMPLE_RATE, CHUNK_SIZE, CHANNELS, DTYPE

logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures audio from a sounddevice input and pushes chunks to an async queue."""

    def __init__(self) -> None:
        self._stream: sd.InputStream | None = None
        self._queue: asyncio.Queue[np.ndarray] = asyncio.Queue(maxsize=64)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._device_id: int | None = None
        self._running: bool = False

    @property
    def running(self) -> bool:
        return self._running

    @property
    def queue(self) -> asyncio.Queue[np.ndarray]:
        return self._queue

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Called by sounddevice from audio thread — must be fast."""
        if status:
            logger.warning("sounddevice status: %s", status)
        chunk = indata[:, 0].copy() if indata.ndim > 1 else indata.copy().flatten()
        try:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, chunk)
        except asyncio.QueueFull:
            pass  # drop oldest-ish — consumer is too slow

    async def start(self, device_id: int | None = None) -> None:
        """Start audio capture stream."""
        if self._running:
            await self.stop()

        self._device_id = device_id
        self._loop = asyncio.get_running_loop()

        # Drain any stale data
        while not self._queue.empty():
            self._queue.get_nowait()

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=CHUNK_SIZE,
            device=device_id,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._running = True
        logger.info("Audio capture started (device=%s, sr=%d, chunk=%d)",
                     device_id, SAMPLE_RATE, CHUNK_SIZE)

    async def stop(self) -> None:
        """Stop audio capture stream."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._running = False
        logger.info("Audio capture stopped")

    async def read_chunk(self) -> np.ndarray:
        """Wait for and return the next audio chunk."""
        return await self._queue.get()
