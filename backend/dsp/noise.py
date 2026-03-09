"""Spectral subtraction noise reduction for real-time audio."""

import numpy as np

from backend.config import NOISE_ALPHA, NOISE_BETA, CHUNK_SIZE


class SpectralNoiseReducer:
    """Spectral subtraction noise reduction.

    Estimates a noise floor from a calibration period, then subtracts
    the noise spectrum from each chunk while preserving phase.
    """

    def __init__(
        self,
        fft_size: int = CHUNK_SIZE,
        alpha: float = NOISE_ALPHA,
        beta: float = NOISE_BETA,
    ) -> None:
        self.fft_size = fft_size
        self.alpha = alpha
        self.beta = beta
        self._noise_profile: np.ndarray | None = None
        self._calibration_frames: list[np.ndarray] = []
        self._calibrating: bool = False
        self._window = np.hanning(fft_size).astype(np.float32)

    @property
    def calibrated(self) -> bool:
        return self._noise_profile is not None

    def start_calibration(self) -> None:
        """Begin noise calibration — collect frames of ambient noise."""
        self._calibration_frames = []
        self._calibrating = True

    def add_calibration_frame(self, chunk: np.ndarray) -> None:
        """Add a frame to the calibration buffer."""
        if self._calibrating:
            self._calibration_frames.append(chunk.copy())

    def finish_calibration(self) -> None:
        """Finalize calibration by averaging collected noise spectra."""
        if not self._calibration_frames:
            self._calibrating = False
            return

        spectra = []
        for frame in self._calibration_frames:
            padded = np.zeros(self.fft_size, dtype=np.float32)
            n = min(len(frame), self.fft_size)
            padded[:n] = frame[:n]
            windowed = padded * self._window
            mag = np.abs(np.fft.rfft(windowed))
            spectra.append(mag)

        self._noise_profile = np.mean(spectra, axis=0).astype(np.float32)
        self._calibration_frames = []
        self._calibrating = False

    def auto_calibrate(self, chunk: np.ndarray, n_frames: int = 20) -> None:
        """Quick auto-calibration from a single chunk (repeated)."""
        self.start_calibration()
        for _ in range(n_frames):
            self.add_calibration_frame(chunk)
        self.finish_calibration()

    def process(self, chunk: np.ndarray) -> np.ndarray:
        """Apply spectral subtraction to a chunk."""
        if self._noise_profile is None:
            return chunk

        padded = np.zeros(self.fft_size, dtype=np.float32)
        n = min(len(chunk), self.fft_size)
        padded[:n] = chunk[:n]

        windowed = padded * self._window
        spectrum = np.fft.rfft(windowed)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)

        # Spectral subtraction with floor
        clean_mag = np.maximum(
            magnitude - self.alpha * self._noise_profile,
            self.beta * magnitude,
        )

        # Reconstruct
        clean_spectrum = clean_mag * np.exp(1j * phase)
        result = np.fft.irfft(clean_spectrum, n=self.fft_size)

        return result[:n].astype(np.float32)

    def set_params(self, alpha: float | None = None, beta: float | None = None) -> None:
        if alpha is not None:
            self.alpha = alpha
        if beta is not None:
            self.beta = beta
