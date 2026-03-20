"""Tests for CardiacFilter — toggle, process, gain."""

import numpy as np
import pytest

from cardiac_dsp import CardiacFilter
from cardiac_dsp.config import CHUNK_SIZE, SAMPLE_RATE


@pytest.fixture
def cardiac_filter() -> CardiacFilter:
    return CardiacFilter()


class TestToggle:
    def test_default_disabled(self, cardiac_filter: CardiacFilter) -> None:
        assert cardiac_filter.enabled is False

    def test_enable(self, cardiac_filter: CardiacFilter) -> None:
        cardiac_filter.enable()
        assert cardiac_filter.enabled is True

    def test_disable(self, cardiac_filter: CardiacFilter) -> None:
        cardiac_filter.enable()
        cardiac_filter.disable()
        assert cardiac_filter.enabled is False

    def test_toggle(self, cardiac_filter: CardiacFilter) -> None:
        result = cardiac_filter.toggle()
        assert result is True
        assert cardiac_filter.enabled is True
        result = cardiac_filter.toggle()
        assert result is False
        assert cardiac_filter.enabled is False


class TestPassthrough:
    def test_disabled_returns_same_chunk(self, cardiac_filter: CardiacFilter) -> None:
        chunk = np.random.randn(CHUNK_SIZE).astype(np.float32) * 0.5
        result = cardiac_filter.process(chunk)
        np.testing.assert_array_equal(result, chunk)

    def test_enabled_modifies_chunk(self, cardiac_filter: CardiacFilter) -> None:
        chunk = np.random.randn(CHUNK_SIZE).astype(np.float32) * 0.5
        cardiac_filter.enable()
        result = cardiac_filter.process(chunk)
        assert not np.array_equal(result, chunk)

    def test_output_dtype_float32(self, cardiac_filter: CardiacFilter) -> None:
        chunk = np.random.randn(CHUNK_SIZE).astype(np.float32) * 0.5
        cardiac_filter.enable()
        result = cardiac_filter.process(chunk)
        assert result.dtype == np.float32

    def test_output_length_matches_input(self, cardiac_filter: CardiacFilter) -> None:
        chunk = np.random.randn(CHUNK_SIZE).astype(np.float32) * 0.5
        cardiac_filter.enable()
        result = cardiac_filter.process(chunk)
        assert len(result) == CHUNK_SIZE


class TestGain:
    def test_set_gain(self, cardiac_filter: CardiacFilter) -> None:
        cardiac_filter.set_gain(2.0)
        assert cardiac_filter.status["gain"] == 2.0

    def test_gain_affects_output(self) -> None:
        f1 = CardiacFilter(gain=1.0)
        f2 = CardiacFilter(gain=0.5)
        f1.enable()
        f2.enable()

        chunk = np.random.randn(CHUNK_SIZE).astype(np.float32) * 0.1
        out1 = f1.process(chunk)
        out2 = f2.process(chunk)

        rms1 = np.sqrt(np.mean(out1 ** 2))
        rms2 = np.sqrt(np.mean(out2 ** 2))
        assert rms2 < rms1


class TestStatus:
    def test_status_keys(self, cardiac_filter: CardiacFilter) -> None:
        s = cardiac_filter.status
        assert "enabled" in s
        assert "sample_rate" in s
        assert "chunk_size" in s
        assert "gain" in s

    def test_status_reflects_state(self, cardiac_filter: CardiacFilter) -> None:
        cardiac_filter.enable()
        cardiac_filter.set_gain(3.0)
        s = cardiac_filter.status
        assert s["enabled"] is True
        assert s["gain"] == 3.0
        assert s["sample_rate"] == SAMPLE_RATE


class TestSampleRate:
    def test_set_sample_rate(self) -> None:
        f = CardiacFilter(sample_rate=48000)
        assert f.status["sample_rate"] == 48000

    def test_change_sample_rate(self, cardiac_filter: CardiacFilter) -> None:
        cardiac_filter.set_sample_rate(48000)
        assert cardiac_filter.status["sample_rate"] == 48000
