"""Configuration constants for the cardiac DSP pipeline."""

# Audio capture
SAMPLE_RATE: int = 44100
CHUNK_SIZE: int = 1024  # samples per chunk (~23.2ms @ 44100 Hz)

# DSP: DC removal
DC_REMOVAL_CUTOFF: float = 5.0  # Hz
DC_REMOVAL_ORDER: int = 2

# DSP: Cardiac bandpass
CARDIAC_LOW_CUT: float = 20.0  # Hz
CARDIAC_HIGH_CUT: float = 250.0  # Hz
CARDIAC_FILTER_ORDER: int = 4

# DSP: Cardiac emphasis bands (freq_start, freq_end, gain_db)
CARDIAC_EMPHASIS_BANDS: list[tuple[float, float, float]] = [
    (20, 60, 6.0),
    (60, 150, 3.0),
]

# Output
DEFAULT_GAIN: float = 1.0
