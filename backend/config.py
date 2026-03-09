"""Configuration constants for audio capture and DSP pipeline."""

# Audio capture
SAMPLE_RATE: int = 44100
CHUNK_SIZE: int = 1024  # samples per chunk (~23.2ms @ 44100 Hz)
CHANNELS: int = 1
DTYPE: str = "float32"

# WebSocket
WS_AUDIO_INTERVAL: float = CHUNK_SIZE / SAMPLE_RATE  # ~23.2ms
VIZ_INTERVAL: float = 0.070  # ~70ms between viz updates
VIZ_FFT_SIZE: int = 1024

# DSP defaults
DC_REMOVAL_CUTOFF: float = 5.0  # Hz
DC_REMOVAL_ORDER: int = 2

# Noise reduction defaults
NOISE_ALPHA: float = 2.0  # spectral subtraction strength
NOISE_BETA: float = 0.02  # spectral floor

# AGC / limiter
AGC_TARGET_RMS: float = 0.15
AGC_TIME_CONSTANT: float = 0.5  # seconds
AGC_SMOOTHING: float = 1.0 - (CHUNK_SIZE / SAMPLE_RATE) / AGC_TIME_CONSTANT
DEFAULT_GAIN: float = 1.0

# Modes
MODES: dict[str, dict] = {
    "cardiac": {
        "low_cut": 20.0,
        "high_cut": 250.0,
        "filter_order": 4,
        "emphasis": {
            # (freq_start, freq_end, gain_db)
            "bands": [(20, 60, 6.0), (60, 150, 3.0)],
        },
    },
    "respiratory": {
        "low_cut": 80.0,
        "high_cut": 1200.0,
        "filter_order": 3,
        "emphasis": {
            "bands": [(100, 300, 3.0), (300, 600, 6.0)],
        },
    },
    "raw": {
        "low_cut": 15.0,
        "high_cut": 2000.0,
        "filter_order": 2,
        "emphasis": {
            "bands": [],
        },
    },
}
