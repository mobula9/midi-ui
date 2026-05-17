#!/usr/bin/env python3
"""batch_annotate.py — annote tous les MIDI du dossier midi/ + midi/more/.

Pour chaque MIDI :
  - séparation des mains (respecte 2 pistes existantes, sinon algo par registre)
  - doigtés (heuristique span-aware)
  - sortie dans midi/annotated/<nom>.mid + <nom>.synthesia
  - si durée > 90 s : découpe en parts (silences ≥ 1 s en priorité, fallback équitable)
    → midi/annotated/<nom>/Part 1.mid + .synthesia, Part 2…
"""
from __future__ import annotations

import sys
import traceback
from copy import deepcopy
from pathlib import Path

import mido

from annotate_midi import (
    Note, MIDDLE_C,
    extract_notes_per_track, group_onsets, split_hands, assign_fingerings,
    write_midi, compute_unique_id, build_finger_hints, write_synthesia_xml,
)
from detect_sections import detect_sections, Section
from humanize import humanize_midi

ROOT = Path(__file__).parent
SRC_DIRS = [ROOT / "midi", ROOT / "midi" / "more"]
OUT_DIR = ROOT / "midi" / "annotated"

LONG_THRESHOLD_S = 90.0     # > 1m30 → on découpe
TARGET_SECTION_S = 45.0     # cible moyenne d'une section
MIN_SECTION_S = 20.0
MAX_SECTION_S = 90.0
SILENCE_MIN_S = 1.0         # silence (vide total) ≥ 1 s = candidat pour split


def get_initial_tempo(mid: mido.MidiFile) -> int:
    """Première tempo en µs/beat (défaut 120 BPM)."""
    for track in mid.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                return msg.tempo
    return 500_000


def get_time_signatures(mid: mido.MidiFile) -> list[tuple[int, int, int]]:
    """Liste des (tick_absolu, numerator, denominator). Toujours au moins (0,4,4)."""
    events: list[tuple[int, int, int]] = []
    for track in mid.tracks:
        abs_tick = 0
        for msg in track:
            abs_tick += msg.time
            if msg.type == "time_signature":
                events.append((abs_tick, msg.numerator, msg.denominator))
    if not events or events[0][0] != 0:
        events.insert(0, (0, 4, 4))
    return sorted(set(events))


def find_section_splits(notes: list[Note], tpb: int, tempo: int,
                        total_ticks: int) -> list[int]:
    """Retourne une liste de ticks où couper le morceau en sections.

    Stratégie :
      1. Cherche les silences ≥ SILENCE_MIN_S (aucune note ne sonne)
      2. Sélectionne ces silences pour produire des sections de ~TARGET_SECTION_S
      3. Si aucune section convenable n'est trouvée, découpe équitablement.
    """
    if not notes:
        return []
    silence_min_ticks = mido.second2tick(SILENCE_MIN_S, tpb, tempo)
    target_ticks = mido.second2tick(TARGET_SECTION_S, tpb, tempo)
    min_ticks = mido.second2tick(MIN_SECTION_S, tpb, tempo)
    max_ticks = mido.second2tick(MAX_SECTION_S, tpb, tempo)

    # Intervalles "sonnants" fusionnés
    intervals = sorted((n.start_tick, n.end_tick) for n in notes)
    merged: list[tuple[int, int]] = [intervals[0]]
    for s, e in intervals[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # Points candidats : milieu de chaque gros silence
    gaps: list[int] = []
    for i in range(len(merged) - 1):
        gap = merged[i + 1][0] - merged[i][1]
        if gap >= silence_min_ticks:
            gaps.append(merged[i][1] + gap // 2)

    splits: list[int] = []
    prev = 0
    if gaps:
        for g in gaps:
            dist = g - prev
            if dist >= min_ticks:
                # Garde ce split s'il est dans la fenêtre [min, max], ou si forcé
                if dist <= max_ticks:
                    splits.append(g)
                    prev = g
                else:
                    # Trop long : insère un split forcé au milieu, puis prend g
                    while dist > max_ticks:
                        forced = prev + target_ticks
                        splits.append(forced)
                        prev = forced
                        dist = g - prev
                    if g - prev >= min_ticks:
                        splits.append(g)
                        prev = g

    # Si rien (ou pas assez de splits pour couvrir le morceau) → fallback équitable
    if not splits or (total_ticks - prev) > max_ticks:
        # Découpe le reste équitablement
        while (total_ticks - prev) > max_ticks:
            forced = prev + target_ticks
            splits.append(forced)
            prev = forced

    return splits


def make_section_notes(notes: list[Note], start_tick: int, end_tick: int) -> list[Note]:
    """Retourne les notes dont l'attaque est dans [start_tick, end_tick), avec
    leurs ticks rebasés à 0. Les notes qui dépassent la fin sont tronquées."""
    out: list[Note] = []
    for n in notes:
        if start_tick <= n.start_tick < end_tick:
            new_end = min(n.end_tick, end_tick)
            out.append(Note(
                pitch=n.pitch, velocity=n.velocity,
                start_tick=n.start_tick - start_tick,
                end_tick=new_end - start_tick,
                hand=n.hand, finger=n.finger,
            ))
    return out


def make_section_mid(mid_in: mido.MidiFile, start_tick: int, end_tick: int) -> mido.MidiFile:
    """Crée un MidiFile "porteur" pour une section (tempo/signature au début)."""
    mid = mido.MidiFile(ticks_per_beat=mid_in.ticks_per_beat)
    # Récupère les events meta en vigueur au début de la section (dernier tempo/sig)
    last_tempo = None
    last_sig = None
    last_key = None
    for track in mid_in.tracks:
        abs_tick = 0
        for msg in track:
            abs_tick += msg.time
            if abs_tick > start_tick:
                break
            if msg.type == "set_tempo":
                last_tempo = msg
            elif msg.type == "time_signature":
                last_sig = msg
            elif msg.type == "key_signature":
                last_key = msg
    meta = mido.MidiTrack()
    if last_tempo:
        meta.append(last_tempo.copy(time=0))
    if last_sig:
        meta.append(last_sig.copy(time=0))
    if last_key:
        meta.append(last_key.copy(time=0))
    meta.append(mido.MetaMessage("end_of_track", time=0))
    mid.tracks.append(meta)
    return mid


def write_pair(mid_in: mido.MidiFile, notes: list[Note], out_mid: Path, title: str,
               tolerance_ticks: int) -> None:
    """Écrit le couple .mid + .synthesia pour une liste de notes annotées,
    avec humanisation appliquée directement sur le MIDI de sortie."""
    R_ordered, L_ordered = write_midi(mid_in, notes, out_mid, tolerance_ticks)

    # Humanisation in-place. Seed dérivé du nom pour reproductibilité par fichier.
    try:
        seed = hash(out_mid.name) % (2**31)
        humanize_midi(out_mid, out_mid, seed=seed)
    except Exception:
        # Si humanize plante (MIDI bizarre), on garde la version non-humanisée
        pass

    parts = []
    if R_ordered:
        parts.append("t1:RA")
    if L_ordered:
        parts.append("t2:LA")
    parts_str = " ".join(parts)
    fhints = build_finger_hints(R_ordered, L_ordered)
    uid = compute_unique_id(out_mid)  # recalculé sur le fichier humanisé
    write_synthesia_xml(out_mid.with_suffix(".synthesia"), uid, title, parts_str, fhints)


def annotate_file(src: Path, out_root: Path) -> dict:
    """Pipeline complète pour un fichier. Retourne un dict de stats."""
    mid = mido.MidiFile(src)
    tpb = mid.ticks_per_beat
    tempo = get_initial_tempo(mid)
    tolerance_ticks = max(1, tpb // 16)  # ~30 ms à 120 BPM
    duration_s = mid.length

    per_track = extract_notes_per_track(mid)
    notes = [n for _, ns in per_track for n in ns]
    if not notes:
        return {"status": "empty", "file": str(src)}
    notes.sort(key=lambda n: (n.start_tick, n.pitch))

    # Séparation des mains
    if len(per_track) == 2:
        (_, ns_a), (_, ns_b) = per_track
        avg_a = sum(n.pitch for n in ns_a) / len(ns_a)
        avg_b = sum(n.pitch for n in ns_b) / len(ns_b)
        R_src, L_src = (ns_a, ns_b) if avg_a > avg_b else (ns_b, ns_a)
        for n in R_src: n.hand = "R"
        for n in L_src: n.hand = "L"
        split_method = "respect-2-tracks"
    else:
        onsets = group_onsets(notes, tolerance_ticks)
        split_hands(onsets, pivot=MIDDLE_C)
        split_method = f"auto-{len(per_track)}tracks"

    R_notes = [n for n in notes if n.hand == "R"]
    L_notes = [n for n in notes if n.hand == "L"]
    assign_fingerings(R_notes, "R", tolerance_ticks)
    assign_fingerings(L_notes, "L", tolerance_ticks)

    # Sortie full
    out_root.mkdir(parents=True, exist_ok=True)
    base_name = src.stem
    full_out = out_root / f"{base_name}.mid"
    write_pair(mid, notes, full_out, title=base_name, tolerance_ticks=tolerance_ticks)

    sections_written = 0
    # Détection structurelle si long
    if duration_s > LONG_THRESHOLD_S:
        total_ticks = max(n.end_tick for n in notes)
        time_sigs = get_time_signatures(mid)
        notes_tuples = [(n.pitch, n.start_tick, n.end_tick) for n in notes]
        # Cible ~ 1 section par 35 s, plafond 7 sections (évite la sur-segmentation)
        target = max(3, min(7, int(duration_s / 35)))
        sections: list[Section] = detect_sections(
            notes_tuples, time_sigs, tpb, total_ticks,
            target_section_count=target,
        )
        if len(sections) >= 2:
            parts_dir = out_root / base_name
            parts_dir.mkdir(parents=True, exist_ok=True)
            for i, sec in enumerate(sections, 1):
                section_notes = make_section_notes(notes, sec.start_tick, sec.end_tick)
                if not section_notes:
                    continue
                section_mid = make_section_mid(mid, sec.start_tick, sec.end_tick)
                start_s = mido.tick2second(sec.start_tick, tpb, tempo)
                end_s = mido.tick2second(sec.end_tick, tpb, tempo)
                # Nom de fichier : "01 - Refrain (32-48s).mid"
                part_label = f"{i:02d} - {sec.label} ({int(start_s)}-{int(end_s)}s)"
                part_path = parts_dir / f"{part_label}.mid"
                write_pair(section_mid, section_notes, part_path,
                           title=f"{base_name} — {part_label}",
                           tolerance_ticks=tolerance_ticks)
                sections_written += 1

    return {
        "status": "ok",
        "file": str(src),
        "duration_s": round(duration_s, 1),
        "notes": len(notes),
        "MD": len(R_notes),
        "MG": len(L_notes),
        "split": split_method,
        "sections": sections_written,
    }


def main() -> None:
    # Collecte les fichiers .mid (.MID inclus, mais on évite midi/annotated)
    files: list[Path] = []
    for d in SRC_DIRS:
        if not d.exists():
            continue
        for p in d.iterdir():
            if p.is_file() and p.suffix.lower() in (".mid", ".midi"):
                files.append(p)
    files.sort()

    print(f"→ {len(files)} fichiers MIDI à annoter")
    print(f"→ Sortie : {OUT_DIR}")
    print()

    ok = 0
    errors: list[tuple[str, str]] = []
    sections_total = 0
    long_total = 0

    for i, f in enumerate(files, 1):
        try:
            stats = annotate_file(f, OUT_DIR)
            if stats["status"] == "ok":
                ok += 1
                if stats["sections"] > 0:
                    sections_total += stats["sections"]
                    long_total += 1
                if i % 20 == 0 or i == len(files):
                    print(f"  [{i:>3}/{len(files)}] {f.name}  ({stats['duration_s']}s, "
                          f"{stats['notes']} notes, {stats['sections']} parts)")
            else:
                errors.append((f.name, "empty"))
        except Exception as e:
            errors.append((f.name, f"{type(e).__name__}: {e}"))

    print()
    print("=" * 60)
    print(f"OK          : {ok}/{len(files)}")
    print(f"Long >1m30  : {long_total} morceaux découpés en {sections_total} parts")
    print(f"Erreurs     : {len(errors)}")
    if errors:
        print("\nDétail des erreurs :")
        for name, err in errors[:20]:
            print(f"  - {name}: {err}")
        if len(errors) > 20:
            print(f"  … et {len(errors) - 20} autres")


if __name__ == "__main__":
    main()
