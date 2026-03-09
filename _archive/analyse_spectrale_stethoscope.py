"""
Analyse spectrale comparative de deux enregistrements de stéthoscope.
Génère deux graphiques :
  1. Comparaison des densités spectrales de puissance (PSD)
  2. Spectrogrammes côte à côte (forme d'onde, spectre complet, zoom cardiaque)

Dépendances : pip install scipy numpy matplotlib soundfile
(soundfile uniquement si tu utilises des .ogg, sinon scipy suffit pour les .wav)
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import welch, spectrogram as sp_spectrogram
import matplotlib
matplotlib.use('Agg')  # Pour générer les images sans affichage — retire cette ligne si tu veux plt.show()
import matplotlib.pyplot as plt

# =============================================================================
# 1. CONFIGURATION — Modifie ces chemins selon tes fichiers
# =============================================================================
FICHIER_1 = "record1.wav"          # Fichier cabine (converti en .wav si nécessaire)
FICHIER_2 = "test_stetho2.wav"     # Fichier PC / Audacity

LABEL_1 = "OGG — Cabine (tablette Linux)"
LABEL_2 = "WAV — PC (Audacity)"

# Si ton fichier est en .ogg, convertis-le d'abord avec ffmpeg :
#   ffmpeg -i record1.ogg -ar 44100 -ac 1 record1.wav

# =============================================================================
# 2. CHARGEMENT DES FICHIERS
# =============================================================================
sr1, data1 = wavfile.read(FICHIER_1)
sr2, data2 = wavfile.read(FICHIER_2)

# Conversion en float mono normalisé
def prepare_audio(data):
    data = data.astype(np.float64)
    if data.ndim > 1:
        data = data.mean(axis=1)
    data = data / (np.max(np.abs(data)) + 1e-10)
    return data

data1 = prepare_audio(data1)
data2 = prepare_audio(data2)

print(f"{LABEL_1}: {sr1} Hz, {len(data1)/sr1:.1f} s")
print(f"{LABEL_2}: {sr2} Hz, {len(data2)/sr2:.1f} s")

# =============================================================================
# 3. CALCUL DES PSD (densité spectrale de puissance)
# =============================================================================
f1, psd1 = welch(data1, sr1, nperseg=4096)
f2, psd2 = welch(data2, sr2, nperseg=4096)

# Énergie par bande
def band_energy(f, psd, flo, fhi):
    mask = (f >= flo) & (f <= fhi)
    return np.sum(psd[mask])

def print_report(label, f, psd, nyq):
    total = np.sum(psd)
    bands = [
        ("20-150 Hz  (S1/S2)",    20,  150),
        ("150-600 Hz (souffles)", 150,  600),
        ("600-2500 Hz (wheezing)", 600, min(2500, nyq - 1)),
        ("2500+ Hz   (bruit)",   2500, nyq - 1),
    ]
    print(f"\n  Répartition énergie — {label}:")
    for name, lo, hi in bands:
        if lo >= nyq:
            continue
        e = band_energy(f, psd, lo, min(hi, nyq - 1))
        print(f"    {name}: {e / total * 100:.1f}%")

print_report(LABEL_1, f1, psd1, sr1 // 2)
print_report(LABEL_2, f2, psd2, sr2 // 2)

# Plancher de bruit
def noise_floor(f, psd, above=1000):
    mask = f >= above
    if mask.any():
        return 10 * np.log10(np.mean(psd[mask]) + 1e-20)
    return None

print(f"\n  Plancher de bruit > 1000 Hz:")
print(f"    {LABEL_1}: {noise_floor(f1, psd1):.1f} dB")
print(f"    {LABEL_2}: {noise_floor(f2, psd2):.1f} dB")

# =============================================================================
# 4. GRAPHIQUE 1 — Comparaison PSD
# =============================================================================
fig_psd, ax = plt.subplots(1, 1, figsize=(14, 5))
fig_psd.patch.set_facecolor('#0e0e1a')
ax.set_facecolor('#12122a')

ax.semilogy(f1, psd1, color='#22dd88', linewidth=1.2, alpha=0.9, label=LABEL_1)
ax.semilogy(f2, psd2, color='#ff6655', linewidth=1.2, alpha=0.9, label=LABEL_2)
ax.axvspan(20, 600, alpha=0.15, color='#ffaa00', label='Bande cardiaque (20–600 Hz)')
ax.axvspan(600, 2500, alpha=0.1, color='#ff4444', label='Bruit / hors bande')

ax.set_xlabel("Fréquence (Hz)", color='#aaaacc')
ax.set_ylabel("Densité spectrale de puissance", color='#aaaacc')
ax.set_title("Comparaison spectrale — OGG (cabine) vs WAV (PC)",
             color='#e0e0ff', fontsize=13, fontweight='bold')
ax.legend(fontsize=10, facecolor='#1a1a2e', edgecolor='#333355', labelcolor='#ccccee')
ax.set_xlim(0, min(max(sr1, sr2) // 2, 5000))
ax.tick_params(colors='#aaaacc')
for spine in ax.spines.values():
    spine.set_color('#333355')

fig_psd.savefig("comparison_psd.png", dpi=150, bbox_inches='tight',
                facecolor=fig_psd.get_facecolor())
print("\n→ comparison_psd.png sauvegardé")

# =============================================================================
# 5. GRAPHIQUE 2 — Spectrogrammes côte à côte
# =============================================================================
fig, axes = plt.subplots(3, 2, figsize=(16, 14))
fig.patch.set_facecolor('#0e0e1a')

# Style commun pour tous les axes
for ax_row in axes:
    for ax in ax_row:
        ax.set_facecolor('#12122a')
        ax.tick_params(colors='#aaaacc')
        ax.xaxis.label.set_color('#aaaacc')
        ax.yaxis.label.set_color('#aaaacc')
        ax.title.set_color('#e0e0ff')
        for spine in ax.spines.values():
            spine.set_color('#333355')

labels = [LABEL_1, LABEL_2]
datasets = [(data1, sr1), (data2, sr2)]

for col, (data, sr) in enumerate(datasets):

    # --- Ligne 0 : Forme d'onde ---
    t = np.arange(len(data)) / sr
    axes[0][col].plot(t, data, color='#22dd88', linewidth=0.3, alpha=0.8)
    axes[0][col].set_title(f"{labels[col]} — Forme d'onde",
                           fontsize=12, fontweight='bold')
    axes[0][col].set_xlabel("Temps (s)")
    axes[0][col].set_ylabel("Amplitude")
    axes[0][col].set_xlim(0, t[-1])

    # --- Ligne 1 : Spectrogramme complet ---
    f_sp, t_sp, Sxx = sp_spectrogram(data, sr, nperseg=4096, noverlap=3072)
    Sxx_db = 10 * np.log10(Sxx + 1e-20)
    vmin = np.percentile(Sxx_db, 5)
    vmax = np.percentile(Sxx_db, 99)

    axes[1][col].pcolormesh(t_sp, f_sp, Sxx_db, shading='gouraud',
                            cmap='inferno', vmin=vmin, vmax=vmax)
    axes[1][col].set_title("Spectrogramme complet", fontsize=12, fontweight='bold')
    axes[1][col].set_xlabel("Temps (s)")
    axes[1][col].set_ylabel("Fréquence (Hz)")
    axes[1][col].set_ylim(0, min(4000, sr // 2))

    # --- Ligne 2 : Zoom cardiaque (20–600 Hz) ---
    mask = f_sp <= 600
    Sxx_heart = Sxx_db[mask, :]
    f_heart = f_sp[mask]
    vmin2 = np.percentile(Sxx_heart, 5)
    vmax2 = np.percentile(Sxx_heart, 99)

    axes[2][col].pcolormesh(t_sp, f_heart, Sxx_heart, shading='gouraud',
                            cmap='magma', vmin=vmin2, vmax=vmax2)
    axes[2][col].set_title("Zoom cardiaque (20–600 Hz)", fontsize=12, fontweight='bold')
    axes[2][col].set_xlabel("Temps (s)")
    axes[2][col].set_ylabel("Fréquence (Hz)")
    axes[2][col].set_ylim(20, 600)

fig.tight_layout(pad=2)
fig.savefig("comparison_spectrograms.png", dpi=150, bbox_inches='tight',
            facecolor=fig.get_facecolor())
print("→ comparison_spectrograms.png sauvegardé")
