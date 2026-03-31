# Stetho — Filtre cardiaque asynchrone

Filtre DSP cardiaque pour stéthoscope en téléconsultation. Prend un fichier WAV en entrée et produit un WAV filtré en sortie.

## Pipeline DSP

1. **Bandpass 20-250 Hz** — Butterworth ordre 4, zero-phase (`sosfiltfilt`)
2. **Emphase fréquentielle** — +6 dB @ 20-60 Hz (S1/S2), +3 dB @ 60-150 Hz
3. **Gain + soft limiter** — gain réglable, `tanh` pour éviter le clipping

## Utilisation

```bash
pip install -r requirements.txt

# Basique
python filter.py input.wav output.wav

# Avec gain
python filter.py input.wav output.wav --gain 2.0
```

## Sortie

```
Entrée    : input.wav
  Format  : 44100 Hz, int16, 20.41s
  RMS     : -7.9 dB
  Peak    : 0.0 dB
Pipeline  :
  1. Bandpass 20-250 Hz (Butterworth ordre 4, zero-phase)
  2. Emphase +6 dB @ 20-60 Hz, +3 dB @ 60-150 Hz
  3. Gain 1.0x + soft limiter (tanh)
Sortie    : output.wav
  RMS     : -14.3 dB
  Peak    : -2.1 dB
OK
```

## Contexte

Le stéthoscope apparaît comme un micro USB/jack standard. Le son capturé est un enregistrement brut qui contient du bruit hors bande. Ce filtre isole la bande cardiaque (20-250 Hz) et accentue les fréquences diagnostiques (S1/S2).

Voir `TECH-Les devices pour les nuls-190326-125749.pdf` pour l'architecture des dispositifs médicaux Tessan.

## Dépendances

- Python 3.10+
- NumPy
- SciPy
