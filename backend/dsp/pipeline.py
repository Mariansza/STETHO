"""DSP pipeline orchestrator — chains all processing stages."""

import numpy as np
from scipy.signal import windows

from backend.config import (
    CHUNK_SIZE,
    DC_REMOVAL_CUTOFF,
    DC_REMOVAL_ORDER,
    DEFAULT_GAIN,
)
from backend.dsp.filters import make_highpass, make_bandpass, RealtimeFilter
from backend.dsp.noise import SpectralNoiseReducer
from backend.dsp.emphasis import build_emphasis_curve, apply_emphasis_inplace
from backend.dsp.modes import get_mode_preset, ModePreset


class DSPPipeline:
    """Complete DSP processing chain for stethoscope audio.

    Stages:
    1. DC removal (HP 5Hz)
    2. Bandpass filter (mode-dependent)
    3. Spectral noise reduction + emphasis (only when noise calibrated, uses overlap-add)
    4. Soft limiter + gain
    """

    def __init__(self, mode: str = "cardiac", sample_rate: int = 44100) -> None:
        self._mode_name = mode
        self._sample_rate = sample_rate
        self._preset: ModePreset = get_mode_preset(mode)
        self._gain: float = DEFAULT_GAIN
        self._passthrough: bool = False

        # Stage 1: DC removal
        self._dc_filter: RealtimeFilter = make_highpass(
            DC_REMOVAL_CUTOFF, DC_REMOVAL_ORDER, self._sample_rate
        )

        # Stage 2: Bandpass
        self._bp_filter: RealtimeFilter = self._build_bandpass()

        # Stage 3: Noise reduction
        self._noise_reducer = SpectralNoiseReducer(fft_size=CHUNK_SIZE)

        # Stage 3b: Emphasis curve
        self._emphasis_curve: np.ndarray = build_emphasis_curve(
            self._preset.emphasis_bands, CHUNK_SIZE, self._sample_rate
        )
        self._emphasis_enabled: bool = len(self._preset.emphasis_bands) > 0

        # Overlap-add state for spectral processing (50% overlap)
        # Hann window satisfies COLA with 50% overlap: w(n) + w(n + N/2) = 1
        self._ola_window = np.hanning(CHUNK_SIZE).astype(np.float32)
        self._ola_prev_half = np.zeros(CHUNK_SIZE // 2, dtype=np.float32)
        self._ola_tail = np.zeros(CHUNK_SIZE // 2, dtype=np.float32)

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def set_sample_rate(self, sample_rate: int) -> None:
        """Update sample rate and rebuild all filters."""
        self._sample_rate = sample_rate
        self._dc_filter = make_highpass(
            DC_REMOVAL_CUTOFF, DC_REMOVAL_ORDER, self._sample_rate
        )
        self._bp_filter = self._build_bandpass()
        self._emphasis_curve = build_emphasis_curve(
            self._preset.emphasis_bands, CHUNK_SIZE, self._sample_rate
        )

    def _build_bandpass(self) -> RealtimeFilter:
        return make_bandpass(
            self._preset.low_cut,
            self._preset.high_cut,
            self._preset.filter_order,
            self._sample_rate,
        )

    def set_mode(self, mode: str) -> None:
        """Switch listening mode — rebuilds filters."""
        self._mode_name = mode
        self._preset = get_mode_preset(mode)
        self._bp_filter = self._build_bandpass()
        self._emphasis_curve = build_emphasis_curve(
            self._preset.emphasis_bands, CHUNK_SIZE, self._sample_rate
        )
        self._emphasis_enabled = len(self._preset.emphasis_bands) > 0

    def set_passthrough(self, enabled: bool) -> None:
        """Enable/disable passthrough (bypass all DSP)."""
        self._passthrough = enabled

    def set_bandpass_params(
        self,
        low_cut: float | None = None,
        high_cut: float | None = None,
        filter_order: int | None = None,
    ) -> None:
        """Override bandpass parameters manually."""
        if low_cut is not None:
            self._preset.low_cut = low_cut
        if high_cut is not None:
            self._preset.high_cut = high_cut
        if filter_order is not None:
            self._preset.filter_order = filter_order
        self._bp_filter = self._build_bandpass()

    def set_gain(self, gain: float) -> None:
        self._gain = gain

    @property
    def noise_reducer(self) -> SpectralNoiseReducer:
        return self._noise_reducer

    @property
    def mode(self) -> str:
        return self._mode_name

    def process(self, chunk: np.ndarray) -> np.ndarray:
        """Process a single audio chunk through the full pipeline."""
        if self._passthrough:
            # Bypass all DSP — just apply gain and soft limit
            x = chunk * self._gain
            return np.clip(x, -1.0, 1.0).astype(np.float32)

        # Stage 1: DC removal
        x = self._dc_filter.process(chunk)

        # Stage 2: Bandpass
        x = self._bp_filter.process(x)

        # Stage 3: Spectral noise reduction + emphasis (only when noise is calibrated)
        if self._noise_reducer.calibrated:
            x = self._spectral_stage(x)

        # Stage 4: Gain + soft limiter (no AGC — let user control gain)
        x = self._output_stage(x)

        return x

    def _spectral_stage(self, chunk: np.ndarray) -> np.ndarray:
        """Spectral processing with proper overlap-add (50% overlap).

        Processes two half-hop frames per chunk to avoid boundary artifacts.
        Hann window with 50% overlap satisfies COLA: w(n) + w(n+N/2) = 1.
        """
        half = CHUNK_SIZE // 2
        output = np.zeros(CHUNK_SIZE, dtype=np.float32)

        for i in range(2):
            # Form analysis frame from previous half + current half
            current_half = chunk[i * half : (i + 1) * half]
            frame = np.concatenate([self._ola_prev_half, current_half])
            self._ola_prev_half = current_half.copy()

            # Analysis window (Hann)
            windowed = frame * self._ola_window
            spectrum = np.fft.rfft(windowed)

            # Noise reduction
            if self._noise_reducer._noise_profile is not None:
                magnitude = np.abs(spectrum)
                phase = np.angle(spectrum)
                clean_mag = np.maximum(
                    magnitude - self._noise_reducer.alpha * self._noise_reducer._noise_profile,
                    self._noise_reducer.beta * magnitude,
                )
                spectrum = clean_mag * np.exp(1j * phase)

            # Emphasis
            if self._emphasis_enabled:
                apply_emphasis_inplace(spectrum, self._emphasis_curve)

            # IFFT — no synthesis window needed (Hann COLA gives unity sum)
            result = np.fft.irfft(spectrum, n=CHUNK_SIZE)

            # Overlap-add: combine with tail from previous frame
            output[i * half : (i + 1) * half] = self._ola_tail + result[:half]
            self._ola_tail = result[half:].copy()

        return output.astype(np.float32)

    def _output_stage(self, chunk: np.ndarray) -> np.ndarray:
        """Apply user gain + soft limiter. No AGC."""
        x = chunk * self._gain

        # Soft limiter (tanh) only if signal exceeds [-1, 1]
        peak = np.max(np.abs(x))
        if peak > 0.8:
            x = np.tanh(x)

        return np.clip(x, -1.0, 1.0).astype(np.float32)
