# Stéthoscope TESSAN — Comment ça fonctionne

## Vue d'ensemble

Le stéthoscope USB apparaît comme un simple microphone sur l'ordinateur. Le backend Python capture le son brut, le fait passer à travers une chaîne de traitement numérique (DSP) en temps réel, puis envoie le résultat au navigateur via WebSocket — à la fois le son traité (pour l'écoute) et des données de visualisation (pour l'affichage).

```
Stéthoscope USB (micro)
        │
        ▼
┌─ Backend Python ──────────────────────────────────────────┐
│                                                           │
│   Capture audio (1024 échantillons toutes les ~23ms)      │
│        │                                                  │
│        ▼                                                  │
│   ┌─ Pipeline DSP ─────────────────────────────────────┐  │
│   │                                                     │  │
│   │   1. Suppression du courant continu (DC)            │  │
│   │   2. Filtre passe-bande (selon le mode)             │  │
│   │   3. Réduction du bruit + emphase fréquentielle     │  │
│   │   4. Contrôle automatique du volume + limiteur      │  │
│   │                                                     │  │
│   └─────────────────────────────────────────────────────┘  │
│        │                                                  │
│        ├──▶ Son traité (binaire)           → toutes les ~23ms │
│        └──▶ Données de visualisation (JSON)→ toutes les ~70ms │
│                                                           │
└───────────────────────────────────────────────────────────┘
        │ WebSocket
        ▼
┌─ Navigateur ──────────────────────────────────────────────┐
│   Lecture audio (AudioWorklet)                            │
│   Forme d'onde + Spectrogramme (Canvas)                   │
│   Contrôles (mode, gain, bruit)                           │
└───────────────────────────────────────────────────────────┘
```

**Latence totale estimée : ~35ms** (bien sous le seuil perceptible de 100ms).

---

## Les 4 étapes du pipeline DSP

Chaque chunk de **1024 échantillons** (soit ~23ms de son à 44 100 Hz) traverse ces 4 étapes dans l'ordre.

### Étape 1 — Suppression du courant continu (DC removal)

**Problème :** Le signal brut du micro USB contient souvent un décalage constant (composante DC) et des vibrations très basses fréquences causées par la manipulation du stéthoscope. Dans les essais initiaux, **44,6% de l'énergie** du signal se trouvait dans ces infra-fréquences inutiles.

**Solution :** Un filtre passe-haut Butterworth d'ordre 2 avec une fréquence de coupure à **5 Hz**. Tout ce qui est en dessous de 5 Hz est éliminé. Le cœur le plus lent bat à ~0,5 Hz (30 bpm), mais les sons cardiaques utiles commencent à 20 Hz — on ne perd donc rien.

### Étape 2 — Filtre passe-bande (selon le mode)

**Rôle :** Ne garder que les fréquences pertinentes pour le type d'auscultation choisi, et supprimer tout le reste.

| Mode | Fréquences gardées | Ordre du filtre | Ce qu'on écoute |
|------|-------------------|-----------------|-----------------|
| **Cardiaque** | 20 – 250 Hz | 4 (pente raide) | S1, S2, souffles, B3/B4 |
| **Respiratoire** | 80 – 1 200 Hz | 3 | Murmure vésiculaire, sibilants, crépitants |
| **Brut** | 15 – 2 000 Hz | 2 (pente douce) | Tout le spectre utile, sans filtrage agressif |

**Comment ça marche techniquement :**

Le filtre est un Butterworth implémenté en **sections de second ordre (SOS)**. On utilise `sosfilt` (filtrage causal, temps réel) et non `sosfiltfilt` (qui nécessiterait tout le signal à l'avance). L'état interne du filtre (`zi`) est conservé d'un chunk à l'autre pour assurer la continuité du signal — sans ça, il y aurait des clics à chaque jonction de chunk.

L'**ordre** du filtre détermine la raideur de la coupure :
- Ordre 2 (brut) : pente douce, transition progressive → moins de distorsion
- Ordre 4 (cardiaque) : pente raide, coupure nette → isolation plus forte des fréquences cardiaques

### Étape 3 — Réduction du bruit + emphase fréquentielle

Ces deux traitements sont **combinés dans une seule transformée de Fourier (FFT)** pour économiser du temps de calcul.

#### 3a. Soustraction spectrale du bruit

**Principe :** On connaît le "profil" du bruit ambiant (capturé lors de la calibration), et on le soustrait du signal en cours.

Concrètement, pour chaque chunk :
1. On passe dans le domaine fréquentiel via FFT
2. On sépare la magnitude (intensité) et la phase (timing) de chaque fréquence
3. On soustrait le profil de bruit de la magnitude :

```
magnitude_propre = max(magnitude - alpha × profil_bruit, beta × magnitude)
```

- **`alpha`** (le curseur "Réduction bruit") contrôle l'agressivité : plus il est élevé, plus on soustrait de bruit
- **`beta`** (fixé à 0.02) est le "plancher spectral" — on ne descend jamais en dessous de 2% du signal original, pour éviter les artefacts musicaux (sons métalliques artificiels)

4. On reconstruit le signal avec la magnitude nettoyée et la phase originale (la phase porte l'information temporelle — on ne la touche pas)

#### 3b. Emphase fréquentielle

Selon le mode, certaines bandes de fréquences sont amplifiées pour mieux entendre les sons pertinents :

**Mode Cardiaque :**
- 20 – 60 Hz : **+6 dB** (× 2 en intensité) → sons S1/S2 fondamentaux
- 60 – 150 Hz : **+3 dB** (× 1.4) → harmoniques cardiaques, souffles

**Mode Respiratoire :**
- 100 – 300 Hz : **+3 dB** → murmure vésiculaire
- 300 – 600 Hz : **+6 dB** → sibilants, crépitants

**Mode Brut :** aucune emphase (courbe plate).

Les transitions entre bandes sont lissées par un fondu cosinus sur 10% de la largeur pour éviter les artefacts.

### Étape 4 — Contrôle automatique du volume (AGC) + limiteur

**AGC (Automatic Gain Control) :** Le volume du stéthoscope varie énormément selon la pression, la position, le patient. L'AGC normalise automatiquement le volume :

1. On mesure le niveau RMS (énergie moyenne) du chunk
2. On calcule le gain nécessaire pour atteindre un niveau cible (RMS = 0.15)
3. On applique un **lissage temporel** (~500ms) pour éviter les changements brusques de volume
4. Le gain est plafonné à ×50 pour ne pas amplifier le silence

**Limiteur doux (soft limiter) :** Après l'AGC et le gain utilisateur, le signal passe par une fonction `tanh` (tangente hyperbolique). Cette fonction :
- Laisse passer les signaux faibles quasi intacts
- Compresse progressivement les signaux forts
- Garantit que la sortie reste dans [-1, +1] — jamais de saturation dure ni de clipping

```
sortie = tanh(signal × gain_AGC × gain_utilisateur)
```

---

## Les contrôles de l'interface

### Curseur "Gain" (0.1× à 5.0×)

Multiplicateur appliqué **après l'AGC**, juste avant le limiteur. C'est le volume "maître" de l'utilisateur.

- **1.0×** : volume par défaut (l'AGC gère seul)
- **< 1.0×** : atténuation — utile si le signal est trop fort même après AGC
- **> 1.0×** : amplification — pousse le signal plus fort dans le limiteur, ce qui augmente le volume perçu mais compresse aussi la dynamique

Comme le limiteur `tanh` est après le gain, monter le gain au-delà de ~3× a un effet de compression : le son paraît plus "plein" mais les pics sont écrasés.

### Curseur "Réduction bruit" (0.5 à 4.0)

C'est le paramètre **alpha** de la soustraction spectrale. Il contrôle combien de fois on soustrait le profil de bruit :

| Valeur | Effet |
|--------|-------|
| **0.5** | Réduction minimale — presque pas de soustraction |
| **1.0** | Soustraction 1:1 du profil de bruit |
| **2.0** (défaut) | Soustraction double — bon compromis bruit/artefacts |
| **3.0 – 4.0** | Réduction agressive — élimine plus de bruit mais risque d'artefacts "musicaux" (sons métalliques) |

**Important :** Ce curseur n'a d'effet que si une calibration du bruit a été effectuée.

### Bouton "Recalibrer le bruit ambiant"

Quand on clique :

1. Le backend **capture 20 chunks** consécutifs (~0,5 seconde de son)
2. Pour chaque chunk, il calcule le spectre de magnitude via FFT
3. Il fait la **moyenne** de ces 20 spectres → c'est le **profil de bruit**
4. Ce profil est ensuite soustrait de chaque chunk futur (étape 3a)

**Quand l'utiliser :**
- Au début de la session, avant de poser le stéthoscope sur le patient
- Quand l'environnement sonore change (ventilation, bruits de fond)
- Le stéthoscope doit capter le bruit ambiant "normal" pendant la calibration — ne pas parler, ne pas toucher le stéthoscope

**Quand ne pas l'utiliser :**
- Pendant qu'on ausculte — le profil capturerait les sons cardiaques/respiratoires comme du "bruit" et les supprimerait ensuite

---

## Les deux visualisations

### Forme d'onde (en haut)

Affiche le signal audio traité en temps réel sous forme d'oscillogramme classique :
- **Axe horizontal** : le temps (1 chunk ≈ 23ms)
- **Axe vertical** : l'amplitude du signal (de -1 à +1)
- **La ligne centrale** : le silence (amplitude 0)

La couleur change selon le mode : rouge (cardiaque), bleu (respiratoire), gris (brut).

Un gradient semi-transparent remplit la zone sous/sur la courbe pour faciliter la lecture. Un léger effet de halo (glow) est appliqué sur la ligne pour la visibilité.

**Ce qu'on peut y lire :**
- Les battements cardiaques apparaissent comme des pics réguliers (S1 = pic large, S2 = pic plus court juste après)
- La respiration apparaît comme des oscillations lentes et régulières
- Le bruit apparaît comme du "fuzz" irrégulier autour de la ligne centrale
- Si le signal sature, la courbe touche les bords haut/bas → baisser le gain

### Spectrogramme (en bas)

Affiche l'**évolution du contenu fréquentiel dans le temps**, sous forme de carte de chaleur :

- **Axe horizontal** : le temps (défile de droite à gauche)
- **Axe vertical** : les fréquences (basses en bas, hautes en haut)
- **La couleur** : l'intensité en dB à cette fréquence à cet instant

Échelle de couleurs :
- **Bleu foncé / noir** : silence ou très faible énergie
- **Cyan / vert** : énergie modérée
- **Jaune / orange** : énergie forte
- **Rouge / blanc** : énergie très forte (pic)

**Ce qu'on peut y lire :**
- **Battements cardiaques** : bandes verticales périodiques concentrées dans les basses fréquences (20–150 Hz)
- **Respiration** : nappes horizontales diffuses dans les moyennes fréquences (200–800 Hz)
- **Souffles cardiaques** : bandes diagonales ou larges dans les fréquences moyennes entre les S1/S2
- **Bruit ambiant** : bande horizontale continue et uniforme (même intensité tout le temps)
- **Crépitants** : points lumineux brefs et isolés

**Fonctionnement technique :** Le spectrogramme ne redessine pas tout à chaque image. Il **décale le contenu existant d'un pixel vers la gauche** puis peint une seule nouvelle colonne à droite. C'est une opération O(1) quel que soit la largeur du canvas — c'est ce qui permet un rafraîchissement fluide à ~14 FPS (une colonne toutes les ~70ms).

---

## Les métriques (barre du bas)

| Métrique | Signification |
|----------|--------------|
| **RMS** | Niveau moyen du signal en dB. Un signal fort est autour de -10 dB, le silence à -50/-60 dB |
| **Peak** | Niveau du pic le plus fort dans le chunk. Si ≥ 0 dB, le signal sature |
| **SNR** | Rapport signal/bruit estimé. Compare l'énergie des 10% de fréquences les plus fortes vs les 50% les plus faibles. Plus c'est élevé, meilleur est le signal |
| **Freq** | Fréquence dominante en Hz — la fréquence avec le plus d'énergie dans le chunk (hors DC) |

Les valeurs sont affichées en police monospace à largeur fixe (`tabular-nums`) pour éviter que l'affichage saute quand les chiffres changent.

---

## Résumé des fichiers clés

| Fichier | Rôle |
|---------|------|
| `backend/config.py` | Toutes les constantes (fréquences, ordres, seuils) |
| `backend/dsp/filters.py` | Filtres Butterworth temps réel avec état |
| `backend/dsp/noise.py` | Soustraction spectrale + calibration |
| `backend/dsp/emphasis.py` | Courbes d'emphase fréquentielle |
| `backend/dsp/pipeline.py` | Orchestration des 4 étapes |
| `backend/dsp/modes.py` | Presets cardiaque / respiratoire / brut |
| `backend/analysis/spectral.py` | Calcul FFT, métriques, données de visualisation |
