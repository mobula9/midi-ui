#!/usr/bin/env python3
"""humanize.py — applique des variations humaines à un MIDI annoté.

Six couches additives :
  1. Vélocité    : jitter ± + emphase temps forts + voix de tête
  2. Articulation: legato (overlap stepwise) / staccato léger en fin de phrase
  3. Indépendance mains : LH décalée ±X ms par rapport à RH sur attaques communes
  4. Timing      : jitter onsets ± + étalement d'accord
  5. Pédale      : CC 64 levée/posée à chaque nouvelle note de basse MG
  6. Rubato      : ralenti sur la dernière mesure de chaque section, retour ensuite

Usage :
    python humanize.py <source.mid> [-o out.mid] [--seed 42]
"""
from __future__ import annotations

import argparse
import hashlib
import random
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import mido

from detect_sections import detect_sections

# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------
VEL_JITTER_STD = 5
BEAT1_BOOST = 12
BEAT_MID_BOOST = 7
OFFBEAT_PENALTY = -2
TOP_VOICE_BOOST = 10
VELOCITY_GAIN = 12              # ajout global à toutes les notes (touché plus appuyé)

TIMING_JITTER_MS = 10
CHORD_SPREAD_MS = 6
HAND_INDEPENDENCE_MS = 8       # désynchro max MG↔MD sur attaques communes

LEGATO_OVERLAP_MS = 12          # extension du note_off en cas de legato
STACCATO_TRIM_RATIO = 0.85      # raccourcissement note finale de phrase

PEDAL_LIFT_LEAD_MS = 5          # lift très bref (résonance qui s'accumule)
PEDAL_BASS_CHANGE_THRESHOLD = 7 # ne lève qu'aux sauts harmoniques ≥ quinte
RUBATO_RIT_PERCENT = 0.015      # ralentit de 1.5 % en fin de section (très très subtil)
RUBATO_ZONE_FRAC = 0.5          # zone du ralentissement = fraction d'une mesure


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ms_to_ticks(ms: float, tpb: int, tempo_us_per_beat: int) -> int:
    return int(round(ms / 1000.0 * 1_000_000 / tempo_us_per_beat * tpb))


def get_initial_tempo(mid: mido.MidiFile) -> int:
    for track in mid.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                return msg.tempo
    return 500_000


def get_time_signature(mid: mido.MidiFile) -> tuple[int, int]:
    for track in mid.tracks:
        for msg in track:
            if msg.type == "time_signature":
                return (msg.numerator, msg.denominator)
    return (4, 4)


def get_time_signature_events(mid: mido.MidiFile) -> list[tuple[int, int, int]]:
    events: list[tuple[int, int, int]] = []
    for track in mid.tracks:
        abs_t = 0
        for msg in track:
            abs_t += msg.time
            if msg.type == "time_signature":
                events.append((abs_t, msg.numerator, msg.denominator))
    if not events or events[0][0] != 0:
        events.insert(0, (0, 4, 4))
    return sorted(set(events))


def identify_track_role(track: mido.MidiTrack) -> str:
    """Renvoie 'R', 'L' ou 'meta' en lisant le nom de piste."""
    for msg in track:
        if msg.type == "track_name":
            name = (msg.name or "").lower()
            if "right" in name or name == "rh":
                return "R"
            if "left" in name or name == "lh":
                return "L"
    return "meta"


def to_abs(track: mido.MidiTrack) -> list[tuple[int, mido.Message | mido.MetaMessage]]:
    out, t = [], 0
    for msg in track:
        t += msg.time
        out.append((t, msg))
    return out


def to_deltas(abs_msgs: list[tuple[int, mido.Message | mido.MetaMessage]]) -> mido.MidiTrack:
    """Reconstruit une track depuis (tick_absolu, message), avec une priorité
    de tri stable : note_off avant note_on à tick identique."""
    prio = {"note_off": 0, "control_change": 1, "set_tempo": 1, "note_on": 2}
    abs_msgs = sorted(abs_msgs, key=lambda e: (e[0], prio.get(e[1].type, 3)))
    track = mido.MidiTrack()
    prev = 0
    for tick, msg in abs_msgs:
        track.append(msg.copy(time=max(0, tick - prev)))
        prev = tick
    return track


# ---------------------------------------------------------------------------
# 1. Vélocité
# ---------------------------------------------------------------------------

def apply_velocity(abs_msgs: list, tpb: int, ts_num: int, rng: random.Random) -> None:
    ticks_per_measure = tpb * ts_num
    groups: dict[int, list[mido.Message]] = defaultdict(list)
    for tick, msg in abs_msgs:
        if msg.type == "note_on" and msg.velocity > 0:
            groups[tick].append(msg)

    for tick, group in groups.items():
        beat_in_measure = (tick % ticks_per_measure) // tpb
        if beat_in_measure == 0:
            beat_adj = BEAT1_BOOST
        elif beat_in_measure == ts_num // 2 and ts_num >= 4:
            beat_adj = BEAT_MID_BOOST
        else:
            beat_adj = OFFBEAT_PENALTY
        max_pitch = max(m.note for m in group)
        for m in group:
            jitter = int(rng.gauss(0, VEL_JITTER_STD))
            top = TOP_VOICE_BOOST if (len(group) > 1 and m.note == max_pitch) else 0
            m.velocity = max(25, min(127, m.velocity + jitter + beat_adj + top + VELOCITY_GAIN))


# ---------------------------------------------------------------------------
# 2. Articulation
# ---------------------------------------------------------------------------

def apply_articulation(abs_msgs: list, tpb: int, tempo: int, rng: random.Random) -> list:
    """Modifie les note_off selon le voisinage :
      - Si la note suivante (même main) est à 1–2 demi-tons et démarre dans
        ≤ 0.25 beat → on prolonge la note actuelle de LEGATO_OVERLAP_MS (overlap).
      - Si la note suivante est à > 1 beat d'écart → on raccourcit la note de
        STACCATO_TRIM_RATIO (phrase qui respire).
    """
    legato_ticks = ms_to_ticks(LEGATO_OVERLAP_MS, tpb, tempo)

    # Identifie les paires note_on → note_off par (pitch, channel)
    on_index: dict[tuple[int, int], list[int]] = defaultdict(list)
    for idx, (_, msg) in enumerate(abs_msgs):
        if msg.type == "note_on" and msg.velocity > 0:
            on_index[(msg.note, msg.channel)].append(idx)

    note_ons: list[tuple[int, int, int]] = []  # (tick, pitch, idx in abs_msgs)
    for idx, (tick, msg) in enumerate(abs_msgs):
        if msg.type == "note_on" and msg.velocity > 0:
            note_ons.append((tick, msg.note, idx))
    note_ons.sort()

    # Pour chaque note_on, trouve la suivante (n'importe quel pitch) — puis sa note_off
    new_abs = list(abs_msgs)
    for i, (tick_i, pitch_i, idx_i) in enumerate(note_ons):
        if i + 1 >= len(note_ons):
            continue
        tick_next, pitch_next, _ = note_ons[i + 1]
        gap_ticks = tick_next - tick_i
        if gap_ticks <= 0:
            continue
        # Cherche le note_off de la note actuelle
        off_idx = _find_matching_off(abs_msgs, pitch_i, idx_i)
        if off_idx is None:
            continue
        off_tick, off_msg = abs_msgs[off_idx]

        # Legato : voisin stepwise ≤ 2 demi-tons, proche temporellement
        if abs(pitch_next - pitch_i) <= 2 and gap_ticks <= tpb // 4:
            new_off_tick = max(off_tick, tick_next + legato_ticks)
            new_abs[off_idx] = (new_off_tick, off_msg)
        # Staccato/respiration : grand espace
        elif gap_ticks > tpb:
            duration = off_tick - tick_i
            trimmed = int(duration * STACCATO_TRIM_RATIO)
            new_abs[off_idx] = (tick_i + max(1, trimmed), off_msg)
    return new_abs


def _find_matching_off(abs_msgs: list, pitch: int, on_idx: int) -> int | None:
    """Trouve l'index du note_off qui ferme le note_on d'index on_idx."""
    on_tick, on_msg = abs_msgs[on_idx]
    channel = on_msg.channel
    for j in range(on_idx + 1, len(abs_msgs)):
        t, m = abs_msgs[j]
        if (m.type == "note_off" or (m.type == "note_on" and m.velocity == 0)) \
                and m.note == pitch and m.channel == channel:
            return j
    return None


# ---------------------------------------------------------------------------
# 3. Indépendance des mains
# ---------------------------------------------------------------------------

def apply_hand_independence(R_abs: list, L_abs: list, tpb: int, tempo: int,
                            rng: random.Random) -> tuple[list, list]:
    """Sur les attaques quasi-simultanées MD/MG, décale la MG de ±max_offset.
    Conserve la durée (le note_off bouge du même montant)."""
    max_off = ms_to_ticks(HAND_INDEPENDENCE_MS, tpb, tempo)
    if max_off <= 0:
        return R_abs, L_abs

    # Collecte les ticks où la MD attaque
    R_attacks = {tick for tick, msg in R_abs if msg.type == "note_on" and msg.velocity > 0}

    new_L = list(L_abs)
    # Trouve pour chaque note_on MG la note_off correspondante et applique un shift
    shifts: dict[tuple[int, int], int] = {}  # (pitch, channel) → shift courant à appliquer au note_off
    for idx, (tick, msg) in enumerate(new_L):
        if msg.type == "note_on" and msg.velocity > 0:
            # Si proche d'une attaque MD (±1/16 de beat) on désynchronise
            window = max(1, tpb // 16)
            close = any(abs(tick - rt) <= window for rt in R_attacks)
            if close:
                shift = rng.randint(-max_off, max_off)
                new_L[idx] = (max(0, tick + shift), msg)
                shifts[(msg.note, msg.channel)] = shift
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            key = (msg.note, msg.channel)
            if key in shifts:
                shift = shifts.pop(key)
                new_L[idx] = (max(0, tick + shift), msg)
    return R_abs, new_L


# ---------------------------------------------------------------------------
# 4. Timing jitter + chord spread
# ---------------------------------------------------------------------------

def apply_timing(abs_msgs: list, tpb: int, tempo: int, rng: random.Random) -> list:
    max_jit = ms_to_ticks(TIMING_JITTER_MS, tpb, tempo)
    max_spread = ms_to_ticks(CHORD_SPREAD_MS, tpb, tempo)
    if max_jit <= 0 and max_spread <= 0:
        return abs_msgs

    type_prio = {"note_off": 0, "note_on": 1}
    sorted_abs = sorted(abs_msgs, key=lambda e: (e[0], type_prio.get(e[1].type, 2)))
    open_shifts: dict[tuple[int, int], int] = {}
    new_abs: list = []
    i, N = 0, len(sorted_abs)
    while i < N:
        tick0, msg0 = sorted_abs[i]
        if msg0.type == "note_on" and msg0.velocity > 0:
            group = [i]
            j = i + 1
            while j < N and sorted_abs[j][0] == tick0 and sorted_abs[j][1].type == "note_on" \
                    and sorted_abs[j][1].velocity > 0:
                group.append(j)
                j += 1
            group.sort(key=lambda k: sorted_abs[k][1].note)
            base_jit = int(rng.gauss(0, max_jit * 0.5)) if max_jit > 0 else 0
            for rank, k in enumerate(group):
                tk, mk = sorted_abs[k]
                spread = rng.randint(0, max_spread) if (len(group) > 1 and max_spread > 0) else 0
                shift = base_jit + (spread * rank // max(1, len(group) - 1))
                new_abs.append((max(0, tk + shift), mk))
                open_shifts[(mk.note, mk.channel)] = shift
            i = j
        elif msg0.type == "note_off" or (msg0.type == "note_on" and msg0.velocity == 0):
            shift = open_shifts.pop((msg0.note, msg0.channel), 0)
            new_abs.append((max(0, tick0 + shift), msg0))
            i += 1
        else:
            new_abs.append((tick0, msg0))
            i += 1
    return new_abs


# ---------------------------------------------------------------------------
# 5. Pédale (CC 64)
# ---------------------------------------------------------------------------

def add_pedal_events(L_abs: list, tpb: int, tempo: int) -> list:
    """Insère des CC 64 (sustain) sur la piste MG :
    levée juste avant chaque nouvelle note de basse, retour pressée à l'attaque.
    """
    lift_lead = ms_to_ticks(PEDAL_LIFT_LEAD_MS, tpb, tempo)

    # Trouve les ticks d'attaques de basse (la plus grave) par groupe
    by_tick: dict[int, list[int]] = defaultdict(list)
    for tick, msg in L_abs:
        if msg.type == "note_on" and msg.velocity > 0:
            by_tick[tick].append(msg.note)
    if not by_tick:
        return L_abs

    sorted_ticks = sorted(by_tick.keys())
    bass_changes: list[int] = []
    last_lifted_bass = None  # basse de référence du dernier "lift"
    for t in sorted_ticks:
        bass = min(by_tick[t])
        if last_lifted_bass is None:
            bass_changes.append(t)
            last_lifted_bass = bass
        elif abs(bass - last_lifted_bass) >= PEDAL_BASS_CHANGE_THRESHOLD:
            bass_changes.append(t)
            last_lifted_bass = bass
        # sinon : on garde la pédale pressée (basse stepwise → on accumule la résonance)

    new_events: list = list(L_abs)
    # Pédale pressée dès la 1ère note
    if bass_changes:
        new_events.append((bass_changes[0],
                           mido.Message("control_change", channel=0, control=64, value=127)))
    for t in bass_changes[1:]:
        # Lève la pédale juste avant
        new_events.append((max(0, t - lift_lead),
                           mido.Message("control_change", channel=0, control=64, value=0)))
        # Repose-la à l'attaque
        new_events.append((t,
                           mido.Message("control_change", channel=0, control=64, value=127)))
    # Lève finale au dernier note_off
    last_off = max((t for t, m in L_abs if m.type == "note_off"), default=None)
    if last_off is not None:
        new_events.append((last_off,
                           mido.Message("control_change", channel=0, control=64, value=0)))
    return new_events


# ---------------------------------------------------------------------------
# 6. Rubato (tempo aux fins de section)
# ---------------------------------------------------------------------------

def add_rubato_events(meta_abs: list, sections, tpb: int, base_tempo: int,
                      ts_num: int) -> list:
    """Ajoute des set_tempo qui ralentissent sur la dernière mesure de chaque
    section, puis restaurent le tempo de base à la mesure suivante.
    """
    if not sections or len(sections) < 2:
        return meta_abs
    rit_zone_ticks = int(tpb * ts_num * RUBATO_ZONE_FRAC)
    slow_tempo = int(base_tempo * (1 + RUBATO_RIT_PERCENT))  # µs/beat plus grand = plus lent
    new_events = list(meta_abs)

    for sec in sections[:-1]:  # pas sur la dernière (outro)
        end = sec.end_tick
        rit_start = max(sec.start_tick, end - rit_zone_ticks)
        new_events.append((rit_start,
                           mido.MetaMessage("set_tempo", tempo=slow_tempo)))
        new_events.append((end,
                           mido.MetaMessage("set_tempo", tempo=base_tempo)))
    return new_events


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def humanize_midi(src_path: Path, dst_path: Path, seed: int | None = None) -> None:
    rng = random.Random(seed)
    mid = mido.MidiFile(src_path)
    tpb = mid.ticks_per_beat
    tempo = get_initial_tempo(mid)
    ts_num, _ = get_time_signature(mid)

    # Détection des sections pour le rubato
    notes_tuples: list[tuple[int, int, int]] = []
    for track in mid.tracks:
        t = 0
        opens: dict[tuple[int, int], int] = {}
        for msg in track:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                opens[(msg.note, msg.channel)] = t
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                k = (msg.note, msg.channel)
                if k in opens:
                    notes_tuples.append((msg.note, opens.pop(k), t))
    total_ticks = max((e for _, _, e in notes_tuples), default=0)
    sections = []
    if total_ticks and mid.length > 90:
        sections = detect_sections(notes_tuples, get_time_signature_events(mid),
                                   tpb, total_ticks,
                                   target_section_count=max(3, min(7, int(mid.length / 35))))

    # Extrait par piste en absolu + identifie les rôles
    track_abs = [to_abs(t) for t in mid.tracks]
    roles = [identify_track_role(t) for t in mid.tracks]

    # 1. Vélocité (R + L)
    for data, role in zip(track_abs, roles):
        if role in ("R", "L"):
            apply_velocity(data, tpb, ts_num, rng)

    # 2. Articulation (R + L), in-place sur la liste retournée
    new_track_abs: list = []
    for data, role in zip(track_abs, roles):
        if role in ("R", "L"):
            new_track_abs.append(apply_articulation(data, tpb, tempo, rng))
        else:
            new_track_abs.append(data)
    track_abs = new_track_abs

    # 3. Indépendance des mains
    R_idx = next((i for i, r in enumerate(roles) if r == "R"), None)
    L_idx = next((i for i, r in enumerate(roles) if r == "L"), None)
    if R_idx is not None and L_idx is not None:
        track_abs[R_idx], track_abs[L_idx] = apply_hand_independence(
            track_abs[R_idx], track_abs[L_idx], tpb, tempo, rng)

    # 4. Timing jitter + chord spread
    track_abs = [
        apply_timing(data, tpb, tempo, rng) if role in ("R", "L") else data
        for data, role in zip(track_abs, roles)
    ]

    # 5. Pédale sur la piste MG
    if L_idx is not None:
        track_abs[L_idx] = add_pedal_events(track_abs[L_idx], tpb, tempo)

    # 6. Rubato sur la piste meta
    meta_idx = next((i for i, r in enumerate(roles) if r == "meta"), 0)
    track_abs[meta_idx] = add_rubato_events(
        track_abs[meta_idx], sections, tpb, tempo, ts_num)

    # Reconstitue le MIDI
    new_mid = mido.MidiFile(ticks_per_beat=tpb)
    for data in track_abs:
        new_mid.tracks.append(to_deltas(data))
    new_mid.save(dst_path)


def regenerate_synthesia(src_syn: Path, dst_mid: Path, dst_syn: Path, title: str) -> None:
    tree = ET.parse(src_syn)
    root = tree.getroot()
    song = root.find(".//Song")
    if song is None:
        raise RuntimeError("Pas d'élément Song dans le .synthesia source")
    new_uid = hashlib.md5(dst_mid.read_bytes()).hexdigest()
    song.set("UniqueId", new_uid)
    song.set("Title", title)
    ET.indent(root, space="  ")
    xml_bytes = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    dst_syn.write_bytes(xml_bytes + b"\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("-o", "--output")
    ap.add_argument("--seed", type=int)
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        raise SystemExit(f"Source introuvable : {src}")
    out_mid = Path(args.output) if args.output else src.with_name(f"{src.stem} [humanisé]{src.suffix}")

    print(f"→ Source : {src}")
    humanize_midi(src, out_mid, seed=args.seed)
    print(f"→ Sortie : {out_mid}")

    src_syn = src.with_suffix(".synthesia")
    if src_syn.exists():
        out_syn = out_mid.with_suffix(".synthesia")
        regenerate_synthesia(src_syn, out_mid, out_syn, out_mid.stem)
        print(f"→ .synthesia : {out_syn}")


if __name__ == "__main__":
    main()
