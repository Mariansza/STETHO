# Stetho

Traitement audio temps réel pour stéthoscope en téléconsultation.

Un stéthoscope branché en jack/USB est capturé par le backend, traité par un pipeline DSP, puis streamé via WebSocket vers une interface web pour écoute et visualisation.

```
Stéthoscope ──→ Backend Python (DSP) ──→ WebSocket ──→ Frontend Next.js (audio + visu)
```

## Stack

- **Backend** : Python 3.12 / FastAPI / sounddevice / NumPy / SciPy
- **Frontend** : Next.js 14 / TypeScript / Tailwind CSS / AudioWorklet / Canvas 2D

## Lancer

```bash
# Backend (localhost:8000)
cd stetho && python -m uvicorn backend.main:app --reload

# Frontend (localhost:3001)
cd stetho/frontend && npm install && npm run dev
```

## Pipeline DSP

Par chunk de 1024 samples @ 44100 Hz :

1. DC removal (HP Butterworth 5 Hz)
2. Passe-bande selon le mode
3. Soustraction spectrale du bruit
4. Emphase fréquentielle selon le mode
5. Soft limiter + AGC

## Modes d'écoute

| Mode | Bande | Emphase | Ordre |
|------|-------|---------|-------|
| Cardiaque | 20–250 Hz | +6 dB @ 20-60 Hz, +3 dB @ 60-150 Hz | 4 |
| Respiratoire | 80–1200 Hz | +6 dB @ 300-600 Hz, +3 dB @ 100-300 Hz | 3 |
| Brut | 15–2000 Hz | Plat | 2 |

## Interface

Forme d'onde temps réel, spectrogramme défilant, sélecteur de périphérique, choix du mode, réglage du gain et réduction de bruit.
