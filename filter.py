"""Filtre cardiaque asynchrone pour stéthoscope.

Prend un fichier WAV en entrée, applique le pipeline DSP cardiaque,
et produit un fichier WAV filtré en sortie.

Pipeline :
1. Bandpass Butterworth ordre 4, 20-250 Hz (sosfiltfilt, zero-phase)
2. Emphase fréquentielle : +6 dB @ 20-60 Hz, +3 dB @ 60-150 Hz
3. Gain + soft limiter (tanh)

Usage :
    python filter.py input.wav output.wav
    python filter.py input.wav output.wav --gain 2.0
"""

import argparse
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt


# --- Configuration cardiaque ---

CARDIAC_LOW_CUT: float = 20.0   # Hz
CARDIAC_HIGH_CUT: float = 250.0  # Hz
FILTER_ORDER: int = 4

EMPHASIS_BANDS: list[tuple[float, float, float]] = [
    (20, 60, 6.0),   # +6 dB — S1/S2
    (60, 150, 3.0),  # +3 dB — bruits cardiaques
]

DEFAULT_GAIN: float = 1.0


# --- Étape 1 : Bandpass ---

def bandpass(data: np.ndarray, sample_rate: int) -> np.ndarray:
    """Butterworth bandpass 20-250 Hz, zero-phase (sosfiltfilt)."""
    nyquist = sample_rate / 2
    low = CARDIAC_LOW_CUT / nyquist
    high = CARDIAC_HIGH_CUT / nyquist
    sos = butter(FILTER_ORDER, [low, high], btype="band", output="sos")
    return sosfiltfilt(sos, data).astype(np.float64)


# --- Étape 2 : Emphase fréquentielle ---

def build_emphasis_curve(n_samples: int, sample_rate: int) -> np.ndarray:
    """Construit la courbe de gain fréquentiel pour l'emphase cardiaque."""
    n_bins = n_samples // 2 + 1
    freqs = np.linspace(0, sample_rate / 2, n_bins)
    curve = np.ones(n_bins, dtype=np.float64)

    for freq_start, freq_end, gain_db in EMPHASIS_BANDS:
        mask = (freqs >= freq_start) & (freqs <= freq_end)
        gain_linear = 10 ** (gain_db / 20.0)

        band_indices = np.where(mask)[0]
        if len(band_indices) == 0:
            continue

        band_gains = np.full(len(band_indices), gain_linear, dtype=np.float64)

        # Cosine taper aux bords (10%) pour transition douce
        taper_len = max(1, len(band_indices) // 10)
        band_gains[:taper_len] = np.linspace(1.0, gain_linear, taper_len)
        band_gains[-taper_len:] = np.linspace(gain_linear, 1.0, taper_len)

        curve[band_indices] = band_gains

    return curve


def apply_emphasis(data: np.ndarray, sample_rate: int) -> np.ndarray:
    """Applique l'emphase fréquentielle via FFT globale."""
    curve = build_emphasis_curve(len(data), sample_rate)
    spectrum = np.fft.rfft(data)
    spectrum *= curve
    return np.fft.irfft(spectrum, n=len(data))


# --- Étape 3 : Gain + soft limiter ---

def apply_gain_and_limiter(data: np.ndarray, gain: float) -> np.ndarray:
    """Applique le gain puis soft limiter (tanh) si nécessaire."""
    x = data * gain
    peak = np.max(np.abs(x))
    if peak > 0.8:
        x = np.tanh(x)
    return np.clip(x, -1.0, 1.0)


# --- Pipeline complète ---

def process(data: np.ndarray, sample_rate: int, gain: float = DEFAULT_GAIN) -> np.ndarray:
    """Pipeline DSP cardiaque complète : bandpass → emphase → gain + limiter."""
    # Convertir en float64 normalisé
    if data.dtype == np.int16:
        data = data.astype(np.float64) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float64) / 2147483648.0
    elif data.dtype != np.float64:
        data = data.astype(np.float64)

    # Mono si stéréo
    if data.ndim > 1:
        data = data.mean(axis=1)

    x = bandpass(data, sample_rate)
    x = apply_emphasis(x, sample_rate)
    x = apply_gain_and_limiter(x, gain)

    return x


# --- Métriques ---

def rms_db(data: np.ndarray) -> float:
    rms = np.sqrt(np.mean(data ** 2) + 1e-10)
    return 20 * np.log10(rms + 1e-10)


def peak_db(data: np.ndarray) -> float:
    return 20 * np.log10(np.max(np.abs(data)) + 1e-10)


# --- CLI ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filtre cardiaque pour stéthoscope — WAV → WAV"
    )
    parser.add_argument("input", help="Fichier WAV d'entrée")
    parser.add_argument("output", help="Fichier WAV de sortie")
    parser.add_argument(
        "--gain", type=float, default=DEFAULT_GAIN,
        help=f"Gain de sortie (défaut: {DEFAULT_GAIN})"
    )
    args = parser.parse_args()

    # Chargement
    try:
        sample_rate, data = wavfile.read(args.input)
    except FileNotFoundError:
        print(f"Erreur : fichier introuvable — {args.input}", file=sys.stderr)
        sys.exit(1)

    original_dtype = data.dtype
    duration = len(data) / sample_rate

    print(f"Entrée    : {args.input}")
    print(f"  Format  : {sample_rate} Hz, {original_dtype}, {duration:.2f}s")

    # Normaliser pour métriques avant
    if data.dtype == np.int16:
        data_norm = data.astype(np.float64) / 32768.0
    elif data.dtype == np.int32:
        data_norm = data.astype(np.float64) / 2147483648.0
    else:
        data_norm = data.astype(np.float64)
    if data_norm.ndim > 1:
        data_norm = data_norm.mean(axis=1)

    print(f"  RMS     : {rms_db(data_norm):.1f} dB")
    print(f"  Peak    : {peak_db(data_norm):.1f} dB")

    # Traitement
    print(f"Pipeline  :")
    print(f"  1. Bandpass {CARDIAC_LOW_CUT:.0f}-{CARDIAC_HIGH_CUT:.0f} Hz (Butterworth ordre {FILTER_ORDER}, zero-phase)")
    print(f"  2. Emphase +6 dB @ 20-60 Hz, +3 dB @ 60-150 Hz")
    print(f"  3. Gain {args.gain}x + soft limiter (tanh)")

    result = process(data, sample_rate, gain=args.gain)

    print(f"Sortie    : {args.output}")
    print(f"  RMS     : {rms_db(result):.1f} dB")
    print(f"  Peak    : {peak_db(result):.1f} dB")

    # Reconvertir au format original
    if original_dtype == np.int16:
        output = (result * 32767).astype(np.int16)
    elif original_dtype == np.int32:
        output = (result * 2147483647).astype(np.int32)
    else:
        output = result.astype(np.float32)

    wavfile.write(args.output, sample_rate, output)
    print("OK")


if __name__ == "__main__":
    main()
