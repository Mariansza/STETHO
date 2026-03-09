"""Listening mode presets for the stethoscope DSP pipeline."""

from dataclasses import dataclass, field
from backend.config import MODES


@dataclass
class EmphasisBand:
    freq_start: float
    freq_end: float
    gain_db: float


@dataclass
class ModePreset:
    name: str
    low_cut: float
    high_cut: float
    filter_order: int
    emphasis_bands: list[EmphasisBand] = field(default_factory=list)


def get_mode_preset(mode_name: str) -> ModePreset:
    """Get a mode preset by name."""
    cfg = MODES.get(mode_name)
    if cfg is None:
        raise ValueError(f"Unknown mode: {mode_name}. Available: {list(MODES.keys())}")

    bands = [
        EmphasisBand(freq_start=b[0], freq_end=b[1], gain_db=b[2])
        for b in cfg["emphasis"]["bands"]
    ]

    return ModePreset(
        name=mode_name,
        low_cut=cfg["low_cut"],
        high_cut=cfg["high_cut"],
        filter_order=cfg["filter_order"],
        emphasis_bands=bands,
    )


def list_modes() -> list[str]:
    return list(MODES.keys())
