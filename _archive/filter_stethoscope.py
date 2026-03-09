import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt


def load_audio(path):
    """Charge un fichier WAV et retourne le sample rate et les données."""
    sample_rate, data = wavfile.read(path)
    return sample_rate, data


def design_bandpass_filter(lowcut, highcut, sample_rate, order=4):
    """Crée un filtre passe-bande Butterworth."""
    nyquist = sample_rate / 2
    low = lowcut / nyquist
    high = highcut / nyquist
    sos = butter(order, [low, high], btype='band', output='sos')
    return sos


def apply_filter(data, sos):
    """Applique le filtre au signal."""
    # Convertir en float pour le traitement
    data_float = data.astype(np.float64)
    filtered = sosfiltfilt(sos, data_float)
    return filtered


def save_audio(path, sample_rate, data, original_dtype):
    """Sauvegarde le signal filtré en WAV."""
    # Normaliser pour éviter le clipping et reconvertir au format original
    max_val = np.max(np.abs(data))
    if max_val > 0:
        # Normaliser selon le type original (int16 = -32768 à 32767)
        if original_dtype == np.int16:
            data = (data / max_val * 32767).astype(np.int16)
        else:
            data = data.astype(original_dtype)
    wavfile.write(path, sample_rate, data)


def main():
    # Paramètres
    input_file = "test_stetho2.wav"
    output_file = "test_stetho_filtered.wav"
    lowcut = 20      # Hz - fréquence basse des sons cardiaques
    highcut = 600    # Hz - fréquence haute des sons cardiaques

    # 1. Charger l'audio
    print(f"Chargement de {input_file}...")
    sample_rate, data = load_audio(input_file)
    original_dtype = data.dtype
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Durée: {len(data)/sample_rate:.2f} secondes")

    # 2. Concevoir le filtre
    print(f"Conception du filtre passe-bande {lowcut}-{highcut} Hz...")
    sos = design_bandpass_filter(lowcut, highcut, sample_rate, order=4)

    # 3. Appliquer le filtre
    print("Application du filtre...")
    filtered_data = apply_filter(data, sos)

    # 4. Sauvegarder
    print(f"Sauvegarde dans {output_file}...")
    save_audio(output_file, sample_rate, filtered_data, original_dtype)

    print("Terminé!")


if __name__ == "__main__":
    main()
