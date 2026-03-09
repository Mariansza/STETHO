"""Real-time spectral analysis for visualization data."""

import numpy as np

from backend.config import SAMPLE_RATE, VIZ_FFT_SIZE


class SpectralAnalyzer:
    """Computes FFT, spectrogram rows, waveform summaries, and metrics."""

    def __init__(self, fft_size: int = VIZ_FFT_SIZE) -> None:
        self.fft_size = fft_size
        self._window = np.hanning(fft_size).astype(np.float32)
        self._freqs = np.fft.rfftfreq(fft_size, 1.0 / SAMPLE_RATE)

    def analyze(self, chunk: np.ndarray) -> dict:
        """Compute all viz data from a processed audio chunk."""
        # Waveform summary (min/max per block for efficient rendering)
        waveform = {
            "min": float(np.min(chunk)),
            "max": float(np.max(chunk)),
        }

        # Spectrogram row: magnitude spectrum in dB
        padded = np.zeros(self.fft_size, dtype=np.float32)
        n = min(len(chunk), self.fft_size)
        padded[:n] = chunk[:n]
        windowed = padded * self._window
        magnitude = np.abs(np.fft.rfft(windowed))
        mag_db = 20 * np.log10(magnitude + 1e-10)

        # Downsample spectrogram to ~128 bins for transport
        target_bins = 128
        if len(mag_db) > target_bins:
            indices = np.linspace(0, len(mag_db) - 1, target_bins, dtype=int)
            spectrogram_row = mag_db[indices].tolist()
        else:
            spectrogram_row = mag_db.tolist()

        # Metrics
        rms = np.sqrt(np.mean(chunk ** 2) + 1e-10)
        rms_db = 20 * np.log10(rms + 1e-10)
        peak = np.max(np.abs(chunk))
        peak_db = 20 * np.log10(peak + 1e-10)

        # Dominant frequency
        dominant_idx = np.argmax(magnitude[1:]) + 1  # skip DC
        dominant_freq = float(self._freqs[dominant_idx])

        # Simple SNR estimate (signal power in top 10% bins vs rest)
        sorted_mag = np.sort(magnitude)
        noise_floor = np.mean(sorted_mag[: len(sorted_mag) // 2]) + 1e-10
        signal_level = np.mean(sorted_mag[-(len(sorted_mag) // 10):]) + 1e-10
        snr = 20 * np.log10(signal_level / noise_floor)

        return {
            "type": "viz",
            "waveform": waveform,
            "spectrogram_row": spectrogram_row,
            "metrics": {
                "rms_db": round(float(rms_db), 1),
                "peak_db": round(float(peak_db), 1),
                "snr": round(float(snr), 1),
                "dominant_freq": round(dominant_freq, 1),
            },
        }
