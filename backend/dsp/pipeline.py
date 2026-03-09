"""DSP pipeline orchestrator — chains all processing stages."""

import numpy as np

from backend.config import (
    SAMPLE_RATE,
    CHUNK_SIZE,
    DC_REMOVAL_CUTOFF,
    DC_REMOVAL_ORDER,
    DEFAULT_GAIN,
    AGC_TARGET_RMS,
    AGC_SMOOTHING,
)
from backend.dsp.filters import make_highpass, make_bandpass, RealtimeFilter
from backend.dsp.noise import SpectralNoiseReducer
from backend.dsp.emphasis import build_emphasis_curve, apply_emphasis_inplace
from backend.dsp.modes import get_mode_preset, ModePreset, EmphasisBand


class DSPPipeline:
    """Complete DSP processing chain for stethoscope audio.

    Stages:
    1. DC removal (HP 5Hz)
    2. Bandpass filter (mode-dependent)
    3. Spectral noise reduction + emphasis (combined FFT)
    4. Soft limiter + AGC
    """

    def __init__(self, mode: str = "cardiac") -> None:
        self._mode_name = mode
        self._preset: ModePreset = get_mode_preset(mode)
        self._gain: float = DEFAULT_GAIN

        # Stage 1: DC removal
        self._dc_filter: RealtimeFilter = make_highpass(
            DC_REMOVAL_CUTOFF, DC_REMOVAL_ORDER, SAMPLE_RATE
        )

        # Stage 2: Bandpass
        self._bp_filter: RealtimeFilter = self._build_bandpass()

        # Stage 3: Noise reduction
        self._noise_reducer = SpectralNoiseReducer(fft_size=CHUNK_SIZE)

        # Stage 3b: Emphasis curve
        self._emphasis_curve: np.ndarray = build_emphasis_curve(
            self._preset.emphasis_bands, CHUNK_SIZE, SAMPLE_RATE
        )
        self._emphasis_enabled: bool = len(self._preset.emphasis_bands) > 0

        # Stage 4: AGC state
        self._agc_gain: float = 1.0
        self._window = np.hanning(CHUNK_SIZE).astype(np.float32)

    def _build_bandpass(self) -> RealtimeFilter:
        return make_bandpass(
            self._preset.low_cut,
            self._preset.high_cut,
            self._preset.filter_order,
            SAMPLE_RATE,
        )

    def set_mode(self, mode: str) -> None:
        """Switch listening mode — rebuilds filters."""
        self._mode_name = mode
        self._preset = get_mode_preset(mode)
        self._bp_filter = self._build_bandpass()
        self._emphasis_curve = build_emphasis_curve(
            self._preset.emphasis_bands, CHUNK_SIZE, SAMPLE_RATE
        )
        self._emphasis_enabled = len(self._preset.emphasis_bands) > 0

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
        # Stage 1: DC removal
        x = self._dc_filter.process(chunk)

        # Stage 2: Bandpass
        x = self._bp_filter.process(x)

        # Stage 3: Spectral noise reduction + emphasis (combined FFT)
        if self._noise_reducer.calibrated or self._emphasis_enabled:
            x = self._spectral_stage(x)

        # Stage 4: AGC + soft limiter
        x = self._agc_limiter(x)

        return x

    def _spectral_stage(self, chunk: np.ndarray) -> np.ndarray:
        """Combined noise reduction and emphasis in a single FFT pass."""
        padded = np.zeros(CHUNK_SIZE, dtype=np.float32)
        n = min(len(chunk), CHUNK_SIZE)
        padded[:n] = chunk[:n]

        windowed = padded * self._window
        spectrum = np.fft.rfft(windowed)

        # Noise reduction in spectral domain
        if self._noise_reducer.calibrated and self._noise_reducer._noise_profile is not None:
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

        result = np.fft.irfft(spectrum, n=CHUNK_SIZE)
        return result[:n].astype(np.float32)

    def _agc_limiter(self, chunk: np.ndarray) -> np.ndarray:
        """Automatic gain control + soft tanh limiter."""
        # AGC: smooth RMS tracking
        rms = np.sqrt(np.mean(chunk ** 2) + 1e-10)
        if rms > 1e-6:
            target_gain = AGC_TARGET_RMS / rms
            # Smooth gain changes
            self._agc_gain = (
                AGC_SMOOTHING * self._agc_gain
                + (1 - AGC_SMOOTHING) * target_gain
            )
        # Clamp AGC gain to avoid excessive amplification
        self._agc_gain = min(self._agc_gain, 50.0)

        # Apply gains
        x = chunk * self._agc_gain * self._gain

        # Soft limiter (tanh)
        x = np.tanh(x)

        return x.astype(np.float32)
