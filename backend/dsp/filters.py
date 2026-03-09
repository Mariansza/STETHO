"""Real-time Butterworth filters using SOS (second-order sections) with state."""

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi


class RealtimeFilter:
    """Stateful Butterworth filter for streaming audio.

    Uses sosfilt with zi state carried between chunks for click-free
    real-time processing.
    """

    def __init__(
        self,
        btype: str,
        order: int,
        cutoff: float | tuple[float, float],
        fs: float,
    ) -> None:
        self._btype = btype
        self._order = order
        self._cutoff = cutoff
        self._fs = fs
        self._sos: np.ndarray | None = None
        self._zi: np.ndarray | None = None
        self._build()

    def _build(self) -> None:
        """Build SOS coefficients and initialize filter state."""
        if self._btype == "bandpass":
            Wn = (self._cutoff[0] / (self._fs / 2), self._cutoff[1] / (self._fs / 2))
        else:
            Wn = self._cutoff / (self._fs / 2)

        # Clamp Wn to valid range
        if isinstance(Wn, tuple):
            Wn = (max(1e-6, min(Wn[0], 1 - 1e-6)), max(1e-6, min(Wn[1], 1 - 1e-6)))
        else:
            Wn = max(1e-6, min(Wn, 1 - 1e-6))

        self._sos = butter(self._order, Wn, btype=self._btype, output="sos")
        # Initialize state for zero initial conditions
        zi = sosfilt_zi(self._sos)
        self._zi = zi * 0.0  # start from silence

    def process(self, chunk: np.ndarray) -> np.ndarray:
        """Filter a chunk of audio, maintaining state between calls."""
        filtered, self._zi = sosfilt(self._sos, chunk, zi=self._zi)
        return filtered.astype(np.float32)

    def reset(self) -> None:
        """Reset filter state (e.g. after parameter change)."""
        self._build()

    def update_params(
        self,
        order: int | None = None,
        cutoff: float | tuple[float, float] | None = None,
    ) -> None:
        """Update filter parameters and rebuild."""
        if order is not None:
            self._order = order
        if cutoff is not None:
            self._cutoff = cutoff
        self._build()


def make_highpass(cutoff: float, order: int, fs: float) -> RealtimeFilter:
    return RealtimeFilter("highpass", order, cutoff, fs)


def make_lowpass(cutoff: float, order: int, fs: float) -> RealtimeFilter:
    return RealtimeFilter("lowpass", order, cutoff, fs)


def make_bandpass(
    low: float, high: float, order: int, fs: float
) -> RealtimeFilter:
    return RealtimeFilter("bandpass", order, (low, high), fs)
