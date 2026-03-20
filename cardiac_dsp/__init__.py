"""cardiac_dsp — Standalone cardiac DSP filter for real-time stethoscope audio.

Quick start:
    from cardiac_dsp import CardiacFilter

    f = CardiacFilter(sample_rate=44100)
    f.enable()
    processed = f.process(raw_chunk)
"""

from .core import CardiacFilter

__version__ = "1.0.0"
__all__ = ["CardiacFilter"]
