"""CardiacFilter — standalone cardiac DSP middleware for real-time stethoscope audio.

Usage:
    from cardiac_dsp import CardiacFilter

    f = CardiacFilter(sample_rate=44100, chunk_size=1024)
    f.enable()

    # In the audio loop:
    processed = f.process(raw_chunk)  # np.ndarray float32

    # Toggle from doctor command:
    f.toggle()
"""

import numpy as np

from .config import (
    SAMPLE_RATE,
    CHUNK_SIZE,
    DC_REMOVAL_CUTOFF,
    DC_REMOVAL_ORDER,
    CARDIAC_LOW_CUT,
    CARDIAC_HIGH_CUT,
    CARDIAC_FILTER_ORDER,
    CARDIAC_EMPHASIS_BANDS,
    DEFAULT_GAIN,
)
from .filters import make_highpass, make_bandpass
from .emphasis import EmphasisBand, build_emphasis_curve, apply_emphasis_inplace


class CardiacFilter:
    """Middleware DSP cardiaque pour stéthoscope temps réel.

    Quand enabled=True :
        DC removal → Bandpass 20-250Hz → Emphase spectrale → Gain + limiter
    Quand enabled=False :
        passthrough (audio inchangé)
    """

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        chunk_size: int = CHUNK_SIZE,
        gain: float = DEFAULT_GAIN,
    ) -> None:
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._gain = gain
        self._enabled = False

        self._build_pipeline()

    def _build_pipeline(self) -> None:
        """Build all DSP stages from current parameters."""
        # Stage 1: DC removal (HP 5 Hz)
        self._dc_filter = make_highpass(
            DC_REMOVAL_CUTOFF, DC_REMOVAL_ORDER, self._sample_rate
        )

        # Stage 2: Cardiac bandpass (20-250 Hz)
        self._bp_filter = make_bandpass(
            CARDIAC_LOW_CUT, CARDIAC_HIGH_CUT,
            CARDIAC_FILTER_ORDER, self._sample_rate,
        )

        # Stage 3: Emphasis curve
        self._emphasis_bands = [
            EmphasisBand(freq_start=b[0], freq_end=b[1], gain_db=b[2])
            for b in CARDIAC_EMPHASIS_BANDS
        ]
        self._emphasis_curve = build_emphasis_curve(
            self._emphasis_bands, self._chunk_size, self._sample_rate
        )

        # Overlap-add state (50% overlap, Hann COLA)
        self._ola_prev_half = np.zeros(self._chunk_size // 2, dtype=np.float32)
        self._ola_tail = np.zeros(self._chunk_size // 2, dtype=np.float32)

    # --- Toggle API (pour le médecin) ---

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def toggle(self) -> bool:
        """Toggle filter on/off. Returns the new state."""
        self._enabled = not self._enabled
        return self._enabled

    # --- Processing ---

    def process(self, chunk: np.ndarray) -> np.ndarray:
        """Traite un chunk PCM float32. Si disabled, retourne le chunk tel quel."""
        if not self._enabled:
            return chunk

        # Stage 1: DC removal
        x = self._dc_filter.process(chunk)

        # Stage 2: Bandpass
        x = self._bp_filter.process(x)

        # Stage 3: Spectral emphasis (overlap-add)
        x = self._spectral_stage(x)

        # Stage 4: Gain + soft limiter
        x = self._output_stage(x)

        return x

    def _spectral_stage(self, chunk: np.ndarray) -> np.ndarray:
        """Spectral emphasis with proper overlap-add (50% overlap).

        Processes two half-hop frames per chunk to avoid boundary artifacts.
        Hann window with 50% overlap satisfies COLA: w(n) + w(n+N/2) = 1.
        """
        half = self._chunk_size // 2
        output = np.zeros(self._chunk_size, dtype=np.float32)
        window = np.hanning(self._chunk_size).astype(np.float32)

        for i in range(2):
            current_half = chunk[i * half : (i + 1) * half]
            frame = np.concatenate([self._ola_prev_half, current_half])
            self._ola_prev_half = current_half.copy()

            # Analysis window (Hann)
            windowed = frame * window
            spectrum = np.fft.rfft(windowed)

            # Emphasis
            apply_emphasis_inplace(spectrum, self._emphasis_curve)

            # IFFT
            result = np.fft.irfft(spectrum, n=self._chunk_size)

            # Overlap-add
            output[i * half : (i + 1) * half] = self._ola_tail + result[:half]
            self._ola_tail = result[half:].copy()

        return output.astype(np.float32)

    def _output_stage(self, chunk: np.ndarray) -> np.ndarray:
        """Apply user gain + soft limiter."""
        x = chunk * self._gain

        peak = np.max(np.abs(x))
        if peak > 0.8:
            x = np.tanh(x)

        return np.clip(x, -1.0, 1.0).astype(np.float32)

    # --- Configuration ---

    def set_gain(self, gain: float) -> None:
        self._gain = gain

    def set_sample_rate(self, sample_rate: int) -> None:
        """Update sample rate and rebuild all filters."""
        self._sample_rate = sample_rate
        self._build_pipeline()

    # --- Status ---

    @property
    def status(self) -> dict:
        """État complet pour monitoring."""
        return {
            "enabled": self._enabled,
            "sample_rate": self._sample_rate,
            "chunk_size": self._chunk_size,
            "gain": self._gain,
        }
