import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, welch, spectrogram
import matplotlib.pyplot as plt
import os


def load_audio(path):
    sample_rate, data = wavfile.read(path)
    # Convertir en float normalisé
    if data.dtype == np.int16:
        data = data.astype(np.float64) / 32768.0
    return sample_rate, data


def bandpass_filter(data, sample_rate, lowcut=20, highcut=600, order=4):
    nyquist = sample_rate / 2
    sos = butter(order, [lowcut / nyquist, highcut / nyquist], btype='band', output='sos')
    return sosfiltfilt(sos, data)


def compute_snr(signal, noise):
    """Estime le SNR en dB."""
    power_signal = np.mean(signal ** 2)
    power_noise = np.mean(noise ** 2)
    if power_noise == 0:
        return float('inf')
    return 10 * np.log10(power_signal / power_noise)


def plot_spectre_comparatif(sr, original, filtered, output_path):
    """Spectre fréquentiel : original vs filtré."""
    fig, ax = plt.subplots(figsize=(12, 5))

    freqs_o, psd_o = welch(original, sr, nperseg=4096)
    freqs_f, psd_f = welch(filtered, sr, nperseg=4096)

    ax.semilogy(freqs_o, psd_o, label='Original', alpha=0.7, color='#888888')
    ax.semilogy(freqs_f, psd_f, label='Filtré (20-600 Hz)', alpha=0.9, color='#e74c3c')

    ax.axvline(20, color='green', linestyle='--', alpha=0.5, label='Coupure basse (20 Hz)')
    ax.axvline(600, color='orange', linestyle='--', alpha=0.5, label='Coupure haute (600 Hz)')

    ax.set_xlabel('Fréquence (Hz)')
    ax.set_ylabel('Densité spectrale de puissance')
    ax.set_title('Spectre fréquentiel - Original vs Filtré')
    ax.set_xlim(0, 2000)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  >>{output_path}")


def plot_spectrogrammes(sr, original, filtered, output_path):
    """Spectrogrammes côte à côte."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # Original
    f1, t1, Sxx1 = spectrogram(original, sr, nperseg=2048, noverlap=1024)
    mask1 = f1 <= 1500
    ax1.pcolormesh(t1, f1[mask1], 10 * np.log10(Sxx1[mask1] + 1e-10), shading='gouraud', cmap='inferno')
    ax1.set_ylabel('Fréquence (Hz)')
    ax1.set_title('Spectrogramme - Original')
    ax1.axhline(20, color='green', linestyle='--', alpha=0.5)
    ax1.axhline(600, color='orange', linestyle='--', alpha=0.5)

    # Filtré
    f2, t2, Sxx2 = spectrogram(filtered, sr, nperseg=2048, noverlap=1024)
    mask2 = f2 <= 1500
    ax2.pcolormesh(t2, f2[mask2], 10 * np.log10(Sxx2[mask2] + 1e-10), shading='gouraud', cmap='inferno')
    ax2.set_ylabel('Fréquence (Hz)')
    ax2.set_xlabel('Temps (s)')
    ax2.set_title('Spectrogramme - Filtré (20-600 Hz)')
    ax2.axhline(20, color='green', linestyle='--', alpha=0.5)
    ax2.axhline(600, color='orange', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  >>{output_path}")


def plot_waveform(sr, original, filtered, output_path):
    """Forme d'onde temporelle : original vs filtré."""
    t = np.arange(len(original)) / sr
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

    ax1.plot(t, original, color='#888888', linewidth=0.3)
    ax1.set_ylabel('Amplitude')
    ax1.set_title('Forme d\'onde - Original')
    ax1.grid(True, alpha=0.3)

    ax2.plot(t, filtered, color='#e74c3c', linewidth=0.3)
    ax2.set_ylabel('Amplitude')
    ax2.set_xlabel('Temps (s)')
    ax2.set_title('Forme d\'onde - Filtré (20-600 Hz)')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  >>{output_path}")


def plot_energy_distribution(sr, original, output_path):
    """Répartition de l'énergie par bande de fréquence."""
    freqs, psd = welch(original, sr, nperseg=4096)

    bands = {
        'Infra (<20 Hz)\nVibrations, manip.': (0, 20),
        'Cardiaque (20-200 Hz)\nS1, S2, B3, B4': (20, 200),
        'Souffles (200-600 Hz)\nSouffles, clics': (200, 600),
        'Hors bande (>600 Hz)\nBruit ambiant': (600, sr / 2),
    }

    energies = {}
    for label, (lo, hi) in bands.items():
        mask = (freqs >= lo) & (freqs < hi)
        energies[label] = np.trapezoid(psd[mask], freqs[mask])

    total = sum(energies.values())
    percentages = {k: v / total * 100 for k, v in energies.items()}

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#95a5a6', '#27ae60', '#e67e22', '#e74c3c']
    bars = ax.bar(range(len(percentages)), list(percentages.values()), color=colors)
    ax.set_xticks(range(len(percentages)))
    ax.set_xticklabels(list(percentages.keys()), fontsize=9)
    ax.set_ylabel('Énergie (%)')
    ax.set_title('Répartition de l\'énergie par bande de fréquence')
    ax.grid(True, alpha=0.3, axis='y')

    for bar, pct in zip(bars, percentages.values()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  >>{output_path}")


def analyse_dynamique(sr, data):
    """Analyse la plage dynamique du signal."""
    rms = np.sqrt(np.mean(data ** 2))
    peak = np.max(np.abs(data))
    crest_factor = peak / rms if rms > 0 else 0
    dynamic_range_db = 20 * np.log10(peak / (np.min(np.abs(data[data != 0])) + 1e-10))
    return rms, peak, crest_factor, dynamic_range_db


def generer_rapport(sr, original, filtered, output_path):
    """Génère un rapport texte avec les métriques clés."""
    noise = original - filtered
    snr = compute_snr(filtered, noise)

    rms_o, peak_o, crest_o, dr_o = analyse_dynamique(sr, original)
    rms_f, peak_f, crest_f, dr_f = analyse_dynamique(sr, filtered)

    # Énergie par bande
    freqs, psd = welch(original, sr, nperseg=4096)
    total_energy = np.trapezoid(psd, freqs)
    cardiac_mask = (freqs >= 20) & (freqs < 600)
    cardiac_energy = np.trapezoid(psd[cardiac_mask], freqs[cardiac_mask])
    cardiac_pct = cardiac_energy / total_energy * 100

    lines = [
        "=" * 60,
        "  RAPPORT D'ANALYSE - SON STÉTHOSCOPE TÉLÉCONSULTATION",
        "=" * 60,
        "",
        f"  Sample rate     : {sr} Hz",
        f"  Durée           : {len(original)/sr:.2f} secondes",
        f"  Filtre appliqué : Butterworth ordre 4, passe-bande 20-600 Hz",
        "",
        "--- QUALITÉ DU SIGNAL ---",
        f"  SNR estimé (filtré vs bruit retiré) : {snr:.1f} dB",
        f"  Énergie dans la bande cardiaque     : {cardiac_pct:.1f}%",
        "",
        "--- DYNAMIQUE ---",
        f"  {'':30s} {'Original':>12s} {'Filtré':>12s}",
        f"  {'RMS':30s} {rms_o:>12.6f} {rms_f:>12.6f}",
        f"  {'Pic':30s} {peak_o:>12.6f} {peak_f:>12.6f}",
        f"  {'Facteur de crête':30s} {crest_o:>12.2f} {crest_f:>12.2f}",
        "",
        "--- INTERPRÉTATION ---",
    ]

    if snr > 15:
        lines.append("  [OK] SNR bon (>15 dB) - signal exploitable pour diagnostic")
    elif snr > 8:
        lines.append("  [!!] SNR moyen (8-15 dB) - écoute possible mais souffles légers potentiellement masqués")
    else:
        lines.append("  [KO] SNR faible (<8 dB) - qualité insuffisante pour diagnostic fiable")

    if cardiac_pct > 60:
        lines.append("  [OK] Majorité de l'énergie dans la bande cardiaque - bon signal")
    elif cardiac_pct > 30:
        lines.append("  [!!] Bruit significatif hors bande cardiaque - filtrage recommandé")
    else:
        lines.append("  [KO] Signal dominé par le bruit - vérifier positionnement du stéthoscope")

    lines += [
        "",
        "--- RECOMMANDATIONS MÉDECIN ---",
        "  1. Casque fermé obligatoire (ex: Beyerdynamic DT 770 Pro 80ohm)",
        "  2. Ne JAMAIS utiliser des haut-parleurs ou du Bluetooth",
        "  3. Écouter dans un environnement calme (<35 dB ambiant)",
        "  4. Comparer signal original ET filtré",
        "  5. Coupler l'écoute avec le spectrogramme visuel si possible",
        "=" * 60,
    ]

    rapport = "\n".join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rapport)
    print(f"  >>{output_path}")
    print()
    print(rapport)


def main():
    # Fichiers source (dans le dossier parent)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    output_dir = base_dir

    input_file = os.path.join(parent_dir, "test_stetho2.wav")

    print(f"Chargement de {input_file}...")
    sr, original = load_audio(input_file)
    print(f"  Sample rate: {sr} Hz | Durée: {len(original)/sr:.2f}s")

    print("Filtrage 20-600 Hz...")
    filtered = bandpass_filter(original, sr)

    print("Génération des graphiques...")
    plot_spectre_comparatif(sr, original, filtered, os.path.join(output_dir, "01_spectre_comparatif.png"))
    plot_spectrogrammes(sr, original, filtered, os.path.join(output_dir, "02_spectrogrammes.png"))
    plot_waveform(sr, original, filtered, os.path.join(output_dir, "03_forme_onde.png"))
    plot_energy_distribution(sr, original, os.path.join(output_dir, "04_energie_par_bande.png"))

    print("Génération du rapport...")
    generer_rapport(sr, original, filtered, os.path.join(output_dir, "rapport_analyse.txt"))

    print("\nAnalyse terminée! Tous les fichiers sont dans le dossier 'analyse/'.")


if __name__ == "__main__":
    main()
