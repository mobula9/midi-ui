#!/usr/bin/env python3
"""detect_sections.py — détection structurelle (intro/couplet/refrain) sur
une liste de Note MIDI.

Approche : matrice de similarité par mesure + détection de nouveauté (noyau
damier de Foote) + clustering par similarité cosinus → étiquetage heuristique.

Pure numpy. Pas de ML.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

import numpy as np

# Constants
MEASURE_KERNEL_L = 8          # taille du noyau damier (en mesures)
MIN_SECTION_MEASURES = 8      # une section fait au moins 8 mesures (≈ 16s en 4/4 @120)
MAX_SECTION_MEASURES = 32     # au plus 32 mesures
SIMILARITY_THRESHOLD = 0.93   # seuil cosinus strict (sinon tout se clusterise)
INTRO_DENSITY_MAX = 0.35      # densité relative max pour appeler "Intro"
OUTRO_DENSITY_MAX = 0.45      # idem pour "Outro"
NON_CHROMA_WEIGHT = 6.0       # amplifie densité/registre vs chroma (chroma constant
                              # sur des progressions pop répétitives)


@dataclass
class Section:
    start_tick: int
    end_tick: int
    label: str          # ex: "Intro", "Couplet 1", "Refrain 1", "Pont"
    cluster_id: int     # 0,1,2... — même id = passages similaires


# ---------------------------------------------------------------------------
# Découpage en mesures
# ---------------------------------------------------------------------------

def measure_boundaries(time_sig_events: list[tuple[int, int, int]],
                       ticks_per_beat: int, total_ticks: int) -> list[int]:
    """Retourne les ticks absolus de début de chaque mesure (jusqu'à total_ticks).

    time_sig_events : liste de (tick, numerator, denominator), au moins [(0, 4, 4)].
    """
    if not time_sig_events:
        time_sig_events = [(0, 4, 4)]
    sigs = sorted(time_sig_events)

    boundaries = [0]
    cur = 0
    while cur < total_ticks:
        # signature active à cet instant
        num, den = 4, 4
        for t, n, d in sigs:
            if t <= cur:
                num, den = n, d
            else:
                break
        measure_ticks = int(num * ticks_per_beat * 4 / den)
        if measure_ticks <= 0:
            break
        cur += measure_ticks
        boundaries.append(cur)
    return boundaries


# ---------------------------------------------------------------------------
# Features par mesure
# ---------------------------------------------------------------------------

def measure_features(notes_with_tick: list[tuple[int, int, int]],
                     boundaries: list[int]) -> np.ndarray:
    """Pour chaque mesure, construit un vecteur (12 chroma + 4 traits).

    notes_with_tick : [(pitch, start_tick, end_tick), ...].
    """
    n_meas = max(0, len(boundaries) - 1)
    feat = np.zeros((n_meas, 16))
    if n_meas == 0:
        return feat

    # Tri pour parcourir efficacement
    notes = sorted(notes_with_tick, key=lambda x: x[1])
    i = 0
    for m in range(n_meas):
        s, e = boundaries[m], boundaries[m + 1]
        # Avance i jusqu'à la première note dont start_tick >= s
        while i < len(notes) and notes[i][1] < s:
            i += 1
        # Récupère toutes les notes qui débutent dans [s, e)
        m_notes: list[tuple[int, int, int]] = []
        j = i
        while j < len(notes) and notes[j][1] < e:
            m_notes.append(notes[j])
            j += 1
        if not m_notes:
            continue

        # Chroma pondéré par durée
        for pitch, st, et in m_notes:
            dur = max(1, et - st)
            feat[m, pitch % 12] += dur
        cn = np.linalg.norm(feat[m, :12])
        if cn > 0:
            feat[m, :12] /= cn

        feat[m, 12] = len(m_notes)                                # densité brute
        pitches = [n[0] for n in m_notes]
        feat[m, 13] = (np.mean(pitches) - 60) / 24                # pitch moyen centré
        feat[m, 14] = (max(pitches) - min(pitches)) / 48          # amplitude
        feat[m, 15] = sum(1 for p in pitches if p < 60) / len(pitches)  # ratio MG

    # Normalise la densité globalement (sur [0,1])
    dmax = feat[:, 12].max()
    if dmax > 0:
        feat[:, 12] /= dmax

    # Amplifie les features non-chroma : sans ça la similarité tonale domine
    # et tout le morceau se clusterise sur la même progression d'accords.
    feat[:, 12:16] *= NON_CHROMA_WEIGHT
    return feat


# ---------------------------------------------------------------------------
# Self-similarity matrix + nouveauté (Foote 2000)
# ---------------------------------------------------------------------------

def cosine_ssm(feat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(feat, axis=1, keepdims=True)
    norms[norms == 0] = 1
    nf = feat / norms
    return nf @ nf.T


def novelty_curve(ssm: np.ndarray, L: int = MEASURE_KERNEL_L) -> np.ndarray:
    """Convolution du noyau damier le long de la diagonale."""
    n = ssm.shape[0]
    if n < L:
        return np.zeros(n)
    half = L // 2
    # Noyau damier ± avec taper gaussien
    kr = np.arange(L) - L / 2 + 0.5
    g = np.exp(-(kr ** 2) / (L / 3.5) ** 2)
    sign = np.outer(np.sign(kr), np.sign(kr))  # +1 sur (haut-gauche, bas-droit), -1 sinon
    kernel = sign * np.outer(g, g)

    novelty = np.zeros(n)
    for t in range(half, n - half):
        sub = ssm[t - half:t + half, t - half:t + half]
        novelty[t] = np.sum(sub * kernel)
    # Smoothing par petite moyenne mobile
    if n >= 5:
        kern = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
        novelty = np.convolve(novelty, kern, mode="same")
    return novelty


def pick_peaks(novelty: np.ndarray, min_dist: int,
               target_count: int | None = None) -> list[int]:
    """Trouve les pics, en respectant une distance min.

    Si target_count est fourni, retourne les ~target_count plus forts ;
    sinon retourne tous ceux dont la valeur > médiane + écart-type / 2.
    """
    n = len(novelty)
    if n < 3:
        return []
    cands = []
    for i in range(1, n - 1):
        if novelty[i] > novelty[i - 1] and novelty[i] >= novelty[i + 1] and novelty[i] > 0:
            cands.append((i, novelty[i]))
    if not cands:
        return []

    if target_count is None:
        thr = float(np.median(novelty) + 0.5 * np.std(novelty))
        cands = [c for c in cands if c[1] >= thr]

    cands.sort(key=lambda x: -x[1])
    chosen: list[int] = []
    for idx, _ in cands:
        if all(abs(idx - c) >= min_dist for c in chosen):
            chosen.append(idx)
        if target_count is not None and len(chosen) >= target_count:
            break
    chosen.sort()
    return chosen


# ---------------------------------------------------------------------------
# Clustering + étiquetage
# ---------------------------------------------------------------------------

def cluster_sections(section_feat: np.ndarray) -> list[int]:
    """Attribue un cluster_id à chaque section par regroupement glouton sur
    similarité cosinus (seuil SIMILARITY_THRESHOLD)."""
    n = section_feat.shape[0]
    if n == 0:
        return []
    norms = np.linalg.norm(section_feat, axis=1, keepdims=True)
    norms[norms == 0] = 1
    nf = section_feat / norms
    sim = nf @ nf.T

    labels = [-1] * n
    next_id = 0
    for i in range(n):
        if labels[i] != -1:
            continue
        labels[i] = next_id
        for j in range(i + 1, n):
            if labels[j] == -1 and sim[i, j] >= SIMILARITY_THRESHOLD:
                labels[j] = next_id
        next_id += 1
    return labels


def name_sections(labels: list[int], densities: np.ndarray,
                  n_total: int) -> list[str]:
    """Étiquette chaque section avec un nom musical lisible."""
    cnt = Counter(labels)
    # Le plus répété ≥ 2 fois → Refrain (s'il existe)
    most_common_id = max(cnt, key=lambda k: cnt[k])
    refrain_id = most_common_id if cnt[most_common_id] >= 2 else None

    # 2e plus répété → "Couplet" (si présent)
    by_freq = sorted(cnt.items(), key=lambda kv: -kv[1])
    couplet_id = by_freq[1][0] if len(by_freq) > 1 and by_freq[1][1] >= 2 else None

    names: list[str] = []
    seen: dict[int, int] = {}
    singleton_idx = 0
    for i, lbl in enumerate(labels):
        seen[lbl] = seen.get(lbl, 0) + 1
        suffix = f" {seen[lbl]}" if cnt[lbl] > 1 else ""

        if lbl == refrain_id:
            names.append(f"Refrain{suffix}")
        elif lbl == couplet_id:
            names.append(f"Couplet{suffix}")
        elif cnt[lbl] == 1:
            singleton_idx += 1
            names.append(f"Section {singleton_idx}")
        else:
            names.append(f"Section{suffix}")

    # Heuristiques de raffinage : Intro et Outro
    if names and densities[0] < INTRO_DENSITY_MAX:
        names[0] = "Intro"
    if len(names) > 1 and densities[-1] < OUTRO_DENSITY_MAX:
        names[-1] = "Outro"

    return names


# ---------------------------------------------------------------------------
# API principale
# ---------------------------------------------------------------------------

def detect_sections(notes_with_tick: list[tuple[int, int, int]],
                    time_sig_events: list[tuple[int, int, int]],
                    ticks_per_beat: int, total_ticks: int,
                    target_section_count: int | None = None) -> list[Section]:
    """Retourne la liste des sections détectées.

    notes_with_tick : [(pitch, start_tick, end_tick), ...].
    time_sig_events : [(tick, num, den), ...]. Vide → 4/4 implicite.
    target_section_count : si fourni, force ~ce nombre de sections (sinon auto).

    Retourne [] si le morceau est trop court pour être segmenté.
    """
    bounds = measure_boundaries(time_sig_events, ticks_per_beat, total_ticks)
    n_meas = len(bounds) - 1
    if n_meas < MIN_SECTION_MEASURES * 2:
        return []  # trop court

    feat = measure_features(notes_with_tick, bounds)
    ssm = cosine_ssm(feat)
    nov = novelty_curve(ssm)
    peaks = pick_peaks(nov, min_dist=MIN_SECTION_MEASURES,
                       target_count=target_section_count)

    # Construit les segments en mesures, en encadrant par 0 et n_meas
    measure_splits = [0] + peaks + [n_meas]
    # Élimine les segments trop courts (fusionne avec le précédent)
    cleaned = [measure_splits[0]]
    for m in measure_splits[1:]:
        if m - cleaned[-1] < MIN_SECTION_MEASURES:
            cleaned[-1] = m
        else:
            cleaned.append(m)
    # Cap les segments trop longs (insère des splits intermédiaires)
    final: list[int] = [cleaned[0]]
    for m in cleaned[1:]:
        gap = m - final[-1]
        if gap > MAX_SECTION_MEASURES:
            n_inserts = gap // MAX_SECTION_MEASURES
            step = gap // (n_inserts + 1)
            for k in range(1, n_inserts + 1):
                final.append(final[-1] + step)
        final.append(m)

    if len(final) < 2:
        return []

    # Feature moyenne par section + clustering
    sec_feats = []
    for i in range(len(final) - 1):
        s, e = final[i], final[i + 1]
        sec_feats.append(feat[s:e].mean(axis=0))
    sec_feats_arr = np.array(sec_feats)

    cluster_ids = cluster_sections(sec_feats_arr)
    names = name_sections(cluster_ids, sec_feats_arr[:, 12], n_total=n_meas)

    # Convertit les mesures en ticks
    sections: list[Section] = []
    for i in range(len(final) - 1):
        s_tick = bounds[final[i]] if final[i] < len(bounds) else bounds[-1]
        e_tick = bounds[final[i + 1]] if final[i + 1] < len(bounds) else total_ticks
        sections.append(Section(
            start_tick=s_tick, end_tick=e_tick,
            label=names[i], cluster_id=cluster_ids[i],
        ))
    return sections
