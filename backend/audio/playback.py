"""Direct audio playback via sounddevice output stream.

Plays processed audio directly to system speakers, bypassing the browser
audio chain entirely. This eliminates crackling caused by WebAudio
buffer boundary artifacts on narrow-band filtered signals.
"""

import logging
import queue
import numpy as np
import sounddevice as sd

from backend.config import CHUNK_SIZE

logger = logging.getLogger(__name__)


class AudioPlayback:
    """Plays processed audio chunks to the default output device."""

    def __init__(self) -> None:
        self._stream: sd.OutputStream | None = None
        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=64)
        self._running: bool = False
        self._sample_rate: int = 44100

    @property
    def running(self) -> bool:
        return self._running

    def _output_callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Called by sounddevice from audio thread — fills output buffer."""
        if status:
            logger.warning("playback status: %s", status)
        try:
            chunk = self._queue.get_nowait()
            # Copy mono signal to all output channels
            n = min(len(chunk), frames)
            for ch in range(outdata.shape[1]):
                outdata[:n, ch] = chunk[:n]
                if n < frames:
                    outdata[n:, ch] = 0.0
        except queue.Empty:
            # No data available — output silence
            outdata[:] = 0.0

    def start(self, sample_rate: int) -> None:
        """Start the output stream at the given sample rate."""
        if self._running:
            self.stop()

        self._sample_rate = sample_rate

        # Drain any stale data
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

        # Find best output device — prefer default, log what we use
        out_dev = sd.default.device[1]
        out_info = sd.query_devices(out_dev)
        out_sr = int(out_info["default_samplerate"])
        out_channels = max(1, min(out_info["max_output_channels"], 2))
        logger.info("Output device: %s (sr=%d, ch=%d)", out_info["name"], out_sr, out_channels)

        self._out_channels = out_channels
        self._out_sr = out_sr
        self._in_sr = sample_rate

        self._stream = sd.OutputStream(
            samplerate=out_sr,
            blocksize=CHUNK_SIZE,
            device=out_dev,
            channels=out_channels,
            dtype="float32",
            callback=self._output_callback,
        )
        self._stream.start()
        self._running = True
        logger.info("Audio playback started (in_sr=%d, out_sr=%d)", sample_rate, out_sr)

    def stop(self) -> None:
        """Stop the output stream."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._running = False
        logger.info("Audio playback stopped")

    def feed(self, chunk: np.ndarray) -> None:
        """Queue a processed audio chunk for playback."""
        if not self._running:
            return
        try:
            self._queue.put_nowait(chunk)
        except queue.Full:
            pass  # drop chunk if consumer is too slow
