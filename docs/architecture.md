# Stetho — Architecture

## Overview

Real-time audio processing prototype for USB stethoscope in teleconsultation.

```
USB Stethoscope → Backend Python (localhost:8000) → WebSocket → Frontend Next.js (localhost:3000)
```

## Backend (Python FastAPI)

- **Audio capture**: `sounddevice` (WASAPI on Windows) captures 1024-sample chunks @ 44100 Hz
- **DSP pipeline** (per chunk):
  1. DC removal — HP Butterworth order 2, 5 Hz cutoff
  2. Bandpass — Butterworth SOS, mode-dependent (cardiac/respiratory/raw)
  3. Spectral noise reduction — FFT-based subtraction with configurable alpha/beta
  4. Frequency emphasis — gain curves per mode, applied in same FFT pass
  5. Soft limiter (tanh) + AGC with ~500ms time constant
- **Spectral analysis**: FFT for spectrogram rows, waveform min/max, metrics (RMS, peak, SNR, dominant freq)
- **WebSocket**: binary PCM frames (~23ms) + JSON viz data (~70ms)

## Frontend (Next.js 14 + TypeScript)

- **Audio playback**: AudioWorklet (`pcm-playback-processor.js`) for gapless playback
- **Visualization**: Canvas 2D — waveform (real-time) + scrolling spectrogram
- **Controls**: mode selection, gain slider, noise reduction, device selector

## Listening Modes

| Mode | Band | Emphasis | Filter Order |
|------|------|----------|-------------|
| Cardiac | 20–250 Hz | +6dB @ 20-60Hz, +3dB @ 60-150Hz | 4 |
| Respiratory | 80–1200 Hz | +6dB @ 300-600Hz, +3dB @ 100-300Hz | 3 |
| Raw | 15–2000 Hz | Flat | 2 |

## Key Design Decisions

- `sosfilt` (causal, real-time) instead of `sosfiltfilt` (offline)
- Filter state (`zi`) carried between chunks for continuity
- AudioWorklet (not ScriptProcessorNode) for gap-free playback
- Spectrogram: shift canvas + paint 1 column = O(1) per frame
- Combined noise reduction + emphasis in single FFT pass

## Running

```bash
# Backend
cd stetho && python -m uvicorn backend.main:app --reload

# Frontend
cd stetho/frontend && npm run dev
```
