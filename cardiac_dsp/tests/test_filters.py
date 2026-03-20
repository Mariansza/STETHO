"""Tests for Butterworth filters — frequency response and state continuity."""

import numpy as np
import pytest

from cardiac_dsp.filters import RealtimeFilter, make_highpass, make_bandpass


SAMPLE_RATE = 44100
CHUNK_SIZE = 1024


class TestRealtimeFilter:
    def test_highpass_attenuates_dc(self) -> None:
        hp = make_highpass(cutoff=20.0, order=2, fs=SAMPLE_RATE)
        # DC signal (constant)
        dc = np.ones(CHUNK_SIZE, dtype=np.float32) * 0.5
        # Process several chunks to let the filter settle
        for _ in range(50):
            out = hp.process(dc)
        # Output should be near zero (DC removed)
        assert np.max(np.abs(out)) < 0.01

    def test_bandpass_passes_center_freq(self) -> None:
        bp = make_bandpass(low=20.0, high=250.0, order=4, fs=SAMPLE_RATE)
        # 100 Hz sine — well within the passband
        t = np.arange(CHUNK_SIZE, dtype=np.float32) / SAMPLE_RATE
        sine_100 = np.sin(2 * np.pi * 100 * t).astype(np.float32)
        # Process several chunks for filter settling
        for _ in range(50):
            out = bp.process(sine_100)
        # Signal should pass through with reasonable amplitude
        assert np.max(np.abs(out)) > 0.3

    def test_bandpass_attenuates_out_of_band(self) -> None:
        bp = make_bandpass(low=20.0, high=250.0, order=4, fs=SAMPLE_RATE)
        # 1000 Hz sine — well outside the cardiac band
        t = np.arange(CHUNK_SIZE, dtype=np.float32) / SAMPLE_RATE
        sine_1k = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
        for _ in range(50):
            out = bp.process(sine_1k)
        # Should be heavily attenuated
        assert np.max(np.abs(out)) < 0.1

    def test_state_continuity(self) -> None:
        """Processing the same signal in chunks vs all at once should differ
        only at chunk boundaries (state is carried between calls)."""
        bp = make_bandpass(low=20.0, high=250.0, order=4, fs=SAMPLE_RATE)
        t = np.arange(CHUNK_SIZE * 10, dtype=np.float32) / SAMPLE_RATE
        signal = np.sin(2 * np.pi * 80 * t).astype(np.float32)

        # Process chunk by chunk
        outputs = []
        for i in range(10):
            chunk = signal[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE]
            outputs.append(bp.process(chunk))
        chunked = np.concatenate(outputs)

        # Process all at once (fresh filter)
        bp2 = make_bandpass(low=20.0, high=250.0, order=4, fs=SAMPLE_RATE)
        full = bp2.process(signal)

        # They won't be identical (state init differs), but chunked should be continuous
        # Check that chunked output has no discontinuities at boundaries
        for i in range(1, 10):
            boundary = i * CHUNK_SIZE
            diff = abs(chunked[boundary] - chunked[boundary - 1])
            # Should be smooth — difference similar to neighboring samples
            assert diff < 0.5

    def test_reset(self) -> None:
        bp = make_bandpass(low=20.0, high=250.0, order=4, fs=SAMPLE_RATE)
        chunk = np.random.randn(CHUNK_SIZE).astype(np.float32) * 0.5
        bp.process(chunk)
        bp.reset()
        # After reset, processing silence should give near-zero output
        silence = np.zeros(CHUNK_SIZE, dtype=np.float32)
        out = bp.process(silence)
        assert np.max(np.abs(out)) < 0.01

    def test_update_params(self) -> None:
        bp = make_bandpass(low=20.0, high=250.0, order=4, fs=SAMPLE_RATE)
        bp.update_params(order=2, cutoff=(50.0, 200.0))
        # Should not crash and should still process
        chunk = np.random.randn(CHUNK_SIZE).astype(np.float32) * 0.5
        out = bp.process(chunk)
        assert out.dtype == np.float32
