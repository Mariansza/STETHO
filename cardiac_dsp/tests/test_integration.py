"""Integration tests — full pipeline with synthetic cardiac-like signals."""

import numpy as np
import pytest
import time

from cardiac_dsp import CardiacFilter
from cardiac_dsp.config import CHUNK_SIZE, SAMPLE_RATE


def make_cardiac_signal(
    freq: float = 40.0,
    duration_chunks: int = 10,
    noise_level: float = 0.1,
    sample_rate: int = SAMPLE_RATE,
    chunk_size: int = CHUNK_SIZE,
) -> list[np.ndarray]:
    """Generate a synthetic cardiac signal: sine + white noise."""
    total_samples = duration_chunks * chunk_size
    t = np.arange(total_samples, dtype=np.float32) / sample_rate
    signal = np.sin(2 * np.pi * freq * t).astype(np.float32) * 0.5
    noise = np.random.randn(total_samples).astype(np.float32) * noise_level
    combined = signal + noise
    return [combined[i * chunk_size : (i + 1) * chunk_size] for i in range(duration_chunks)]


class TestFullPipeline:
    def test_process_multiple_chunks(self) -> None:
        """Process a series of chunks without errors."""
        f = CardiacFilter()
        f.enable()
        chunks = make_cardiac_signal()
        for chunk in chunks:
            out = f.process(chunk)
            assert out.dtype == np.float32
            assert len(out) == CHUNK_SIZE
            assert np.all(np.isfinite(out))

    def test_cardiac_signal_preserved(self) -> None:
        """A 40 Hz sine (cardiac range) should have significant energy after filtering."""
        f = CardiacFilter()
        f.enable()

        chunks = make_cardiac_signal(freq=40.0, duration_chunks=50, noise_level=0.0)

        # Let the filter settle
        for chunk in chunks[:40]:
            f.process(chunk)

        # Measure output energy on settled chunks
        outputs = [f.process(chunk) for chunk in chunks[40:]]
        output_signal = np.concatenate(outputs)
        rms = np.sqrt(np.mean(output_signal ** 2))

        assert rms > 0.01

    def test_out_of_band_attenuated(self) -> None:
        """A 1000 Hz sine (outside cardiac band) should be heavily attenuated."""
        f = CardiacFilter()
        f.enable()

        chunks = make_cardiac_signal(freq=1000.0, duration_chunks=50, noise_level=0.0)

        for chunk in chunks[:40]:
            f.process(chunk)

        outputs = [f.process(chunk) for chunk in chunks[40:]]
        output_signal = np.concatenate(outputs)
        rms = np.sqrt(np.mean(output_signal ** 2))

        assert rms < 0.01

    def test_toggle_during_processing(self) -> None:
        """Toggling mid-stream should not crash or produce NaN."""
        f = CardiacFilter()
        chunks = make_cardiac_signal(duration_chunks=20)

        for i, chunk in enumerate(chunks):
            if i == 5:
                f.enable()
            if i == 10:
                f.disable()
            if i == 15:
                f.toggle()
            out = f.process(chunk)
            assert np.all(np.isfinite(out))
            assert len(out) == CHUNK_SIZE

    def test_output_bounded(self) -> None:
        """Output should always be in [-1, 1] thanks to the soft limiter."""
        f = CardiacFilter(gain=5.0)
        f.enable()
        chunks = make_cardiac_signal(noise_level=0.5)
        for chunk in chunks:
            out = f.process(chunk)
            assert np.all(out >= -1.0)
            assert np.all(out <= 1.0)


class TestLatency:
    def test_process_latency(self) -> None:
        """process() should take less than 5ms per chunk."""
        f = CardiacFilter()
        f.enable()

        chunk = np.random.randn(CHUNK_SIZE).astype(np.float32) * 0.5

        # Warm up
        for _ in range(10):
            f.process(chunk)

        # Measure
        times = []
        for _ in range(100):
            start = time.perf_counter()
            f.process(chunk)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        avg_ms = np.mean(times) * 1000
        assert avg_ms < 5.0, f"Average latency {avg_ms:.2f}ms exceeds 5ms target"
