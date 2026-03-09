# Stetho — Auscultation temps réel

Prototype de traitement audio temps réel pour stéthoscope USB en téléconsultation.

## Stack

- **Backend** : Python 3.12 / FastAPI / WebSocket / sounddevice / NumPy / SciPy
- **Frontend** : Next.js 14 / TypeScript / Tailwind CSS / Web Audio API (AudioWorklet) / Canvas 2D
- Pas de BDD — tout en local

## Structure

```
stetho/
├── backend/
│   ├── main.py              # FastAPI + endpoints /api/health, /api/devices, /ws/audio
│   ├── config.py            # Constantes (sample rate 44100, chunk 1024, modes)
│   ├── audio/               # Capture sounddevice + découverte périphériques
│   ├── dsp/                 # Pipeline DSP : filters, noise, emphasis, modes, pipeline
│   ├── analysis/            # Analyse spectrale (FFT, métriques)
│   └── websocket/           # Handler WS + protocole binaire/JSON
├── frontend/
│   ├── public/worklets/     # AudioWorklet (pcm-playback-processor.js)
│   └── src/
│       ├── app/             # Page principale Next.js
│       ├── components/      # header, control-panel, waveform, spectrogram, etc.
│       ├── hooks/           # use-websocket, use-audio-playback, use-canvas-renderer
│       ├── lib/             # ws-protocol, constants
│       └── types/           # Types TypeScript
├── docs/architecture.md
└── _archive/                # Anciens essais (filtrage offline)
```

## Commandes

```bash
# Backend
cd stetho && python -m uvicorn backend.main:app --reload

# Frontend
cd stetho/frontend && npm run dev

# Build frontend
cd stetho/frontend && npm run build
```

## Architecture DSP (pipeline.py)

5 étapes par chunk de 1024 samples @ 44100 Hz :
1. DC removal — HP Butterworth ordre 2, 5 Hz
2. Passe-bande — Butterworth SOS selon mode (sosfilt avec état zi)
3. Soustraction spectrale du bruit (FFT, alpha/beta réglables)
4. Emphase fréquentielle (combinée dans la même FFT que étape 3)
5. Soft limiter (tanh) + AGC (~500ms)

## Modes d'écoute

| Mode | Bande | Emphase | Ordre |
|------|-------|---------|-------|
| Cardiaque | 20–250 Hz | +6dB @ 20-60Hz, +3dB @ 60-150Hz | 4 |
| Respiratoire | 80–1200 Hz | +6dB @ 300-600Hz, +3dB @ 100-300Hz | 3 |
| Brut | 15–2000 Hz | Plat | 2 |

## Protocole WebSocket

- **Backend → Frontend** : binaire (PCM float32 LE avec seq uint32) ~23ms + JSON viz ~70ms
- **Frontend → Backend** : JSON (set_mode, set_params, set_device, start/stop_capture, etc.)

## Conventions

### Python (backend)
- Python 3.12, type hints obligatoires
- snake_case fichiers/fonctions, PascalCase classes
- sosfilt (temps réel, causal) — jamais sosfiltfilt (offline)
- État des filtres (zi) porté entre chunks

### TypeScript (frontend)
- Strict mode
- kebab-case fichiers, PascalCase composants
- Composants fonctionnels + hooks uniquement
- AudioWorklet obligatoire (pas ScriptProcessorNode)

## Points d'attention

- Le stéthoscope apparaît comme un micro USB standard
- Latence cible < 100ms (estimée ~35ms)
- Changement de paramètres filtres → reset zi via sosfilt_zi
- Spectrogramme : shift canvas + paint 1 colonne = O(1) par frame

## Documentation

Pour l'architecture complète, voir `docs/architecture.md`.
