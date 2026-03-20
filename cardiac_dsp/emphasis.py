"""Frequency emphasis curves applied in the spectral domain."""

from dataclasses import dataclass

import numpy as np


@dataclass
class EmphasisBand:
    freq_start: float
    freq_end: float
    gain_db: float


def build_emphasis_curve(
    bands: list[EmphasisBand],
    fft_size: int,
    sample_rate: float,
) -> np.ndarray:
    """Build a gain curve in the frequency domain for emphasis.

    Returns an array of length fft_size//2 + 1 (rfft bins) with
    linear gain values (1.0 = unity).
    """
    n_bins = fft_size // 2 + 1
    freqs = np.linspace(0, sample_rate / 2, n_bins)
    curve = np.ones(n_bins, dtype=np.float32)

    for band in bands:
        mask = (freqs >= band.freq_start) & (freqs <= band.freq_end)
        gain_linear = 10 ** (band.gain_db / 20.0)

        # Smooth transitions at band edges (simple cosine taper)
        band_indices = np.where(mask)[0]
        if len(band_indices) == 0:
            continue

        band_gains = np.ones(len(band_indices), dtype=np.float32) * gain_linear

        # Taper first/last 10% of the band for smooth transition
        taper_len = max(1, len(band_indices) // 10)
        taper_in = np.linspace(1.0, gain_linear, taper_len)
        taper_out = np.linspace(gain_linear, 1.0, taper_len)
        band_gains[:taper_len] = taper_in
        band_gains[-taper_len:] = taper_out

        curve[band_indices] = band_gains

    return curve


def apply_emphasis_inplace(
    spectrum: np.ndarray,
    emphasis_curve: np.ndarray,
) -> np.ndarray:
    """Multiply a complex spectrum by the emphasis gain curve."""
    spectrum *= emphasis_curve
    return spectrum
