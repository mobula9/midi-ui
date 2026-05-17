#!/usr/bin/env python3
"""annotate_midi.py

Lit un fichier MIDI brut, sépare les mains (gauche / droite) et produit :
  1. Un MIDI à 3 pistes : Tempo Map, Right Hand, Left Hand.
  2. Un fichier compagnon `.synthesia` (XML) contenant les attributs `Parts`
     et `FingerHints` lus par Synthesia.

Format Synthesia (cf. https://github.com/Synthesia-LLC/metadata-editor/wiki) :
- Le `.synthesia` référence le MIDI par `UniqueId` = base64(MD5(bytes du MIDI)).
- `Parts` (Synthesia ≥ 10) : `t1:RA t2:LA` → toute la piste 1 = main droite,
  toute la piste 2 = main gauche. (Tracks sont zero-based ; track 0 = tempo.)
- `FingerHints` : une chaîne unique où chaque chiffre s'applique à la note
  suivante (ordre physique des note_on dans la piste).
    1–5 = MG (1 pouce … 5 auriculaire),  6,7,8,9,0 = MD (6 pouce … 0 auriculaire).
  `tN:` change de piste, `mN:` change de mesure, `-` saute une note,
  `s` indique un changement de doigt sur la même note (substitution).

Répertoire ciblé : pop / variété (mélodie MD + accords MG).

Usage :
    python annotate_midi.py entree.mid              # → entree.annotated.mid + entree.annotated.synthesia
    python annotate_midi.py entree.mid -o out.mid
    python annotate_midi.py entree.mid --no-fingering
"""

from __future__ import annotations

import argparse
import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import mido

MIDDLE_C = 60  # C4 — pivot par défaut entre les deux mains


@dataclass
class Note:
    pitch: int
    velocity: int
    start_tick: int
    end_tick: int
    hand: str | None = None    # 'R' ou 'L'
    finger: int | None = None  # 1..5


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_notes_per_track(mid: mido.MidiFile) -> list[tuple[int, list[Note]]]:
    """Retourne [(track_index, notes)] uniquement pour les pistes ayant des notes."""
    per_track: list[tuple[int, list[Note]]] = []
    for ti, track in enumerate(mid.tracks):
        abs_tick = 0
        open_notes: dict[tuple[int, int], tuple[int, int]] = {}
        notes: list[Note] = []
        for msg in track:
            abs_tick += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                open_notes[(msg.note, msg.channel)] = (abs_tick, msg.velocity)
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                key = (msg.note, msg.channel)
                if key in open_notes:
                    start, vel = open_notes.pop(key)
                    notes.append(Note(msg.note, vel, start, abs_tick))
        if notes:
            notes.sort(key=lambda n: (n.start_tick, n.pitch))
            per_track.append((ti, notes))
    return per_track


def extract_notes(mid: mido.MidiFile) -> list[Note]:
    """Aplatit toutes les pistes en une seule liste."""
    all_notes: list[Note] = []
    for _, notes in extract_notes_per_track(mid):
        all_notes.extend(notes)
    all_notes.sort(key=lambda n: (n.start_tick, n.pitch))
    return all_notes


def group_onsets(notes: list[Note], tolerance_ticks: int) -> list[list[Note]]:
    """Regroupe les notes qui démarrent quasi-simultanément (un onset = accord ou note seule)."""
    if not notes:
        return []
    groups: list[list[Note]] = []
    current = [notes[0]]
    for n in notes[1:]:
        if n.start_tick - current[0].start_tick <= tolerance_ticks:
            current.append(n)
        else:
            groups.append(current)
            current = [n]
    groups.append(current)
    return groups


# ---------------------------------------------------------------------------
# Séparation des mains
# ---------------------------------------------------------------------------

def split_hands(onsets: list[list[Note]], pivot: int = MIDDLE_C) -> None:
    """Annote chaque note avec hand='R' ou 'L'.

    Stratégie (adaptée pop/variété) :
    1. Pour un onset à plusieurs notes : si l'écart total ≤ octave → une seule
       main (choisie par registre). Sinon on coupe sur le plus grand intervalle.
    2. Pour une note seule : registre + continuité avec la dernière note de
       chaque main (évite les sauts de main artificiels).
    """
    last_R: int | None = None
    last_L: int | None = None

    for group in onsets:
        group.sort(key=lambda n: n.pitch)
        pitches = [n.pitch for n in group]

        if len(group) == 1:
            n = group[0]
            if n.pitch >= pivot + 7:
                n.hand = "R"
            elif n.pitch <= pivot - 5:
                n.hand = "L"
            else:
                # Zone ambiguë : continuité
                if last_R is not None and last_L is not None:
                    n.hand = "R" if abs(n.pitch - last_R) <= abs(n.pitch - last_L) else "L"
                elif last_R is not None:
                    n.hand = "R" if abs(n.pitch - last_R) <= 12 else "L"
                elif last_L is not None:
                    n.hand = "L" if abs(n.pitch - last_L) <= 12 else "R"
                else:
                    n.hand = "R" if n.pitch >= pivot else "L"
        else:
            span = pitches[-1] - pitches[0]
            if span <= 12:
                # Tout dans une octave → une seule main, choisie par registre
                center = sum(pitches) / len(pitches)
                hand = "R" if center >= pivot else "L"
                for n in group:
                    n.hand = hand
            else:
                # Cherche le plus gros écart pour couper
                max_gap, split_idx = 0, 0
                for i in range(len(pitches) - 1):
                    gap = pitches[i + 1] - pitches[i]
                    if gap > max_gap:
                        max_gap, split_idx = gap, i
                if max_gap >= 5:  # quinte ou plus = vrai trou entre mains
                    for i, n in enumerate(group):
                        n.hand = "L" if i <= split_idx else "R"
                else:
                    for n in group:
                        n.hand = "R" if n.pitch >= pivot else "L"

        R_pitches = [n.pitch for n in group if n.hand == "R"]
        L_pitches = [n.pitch for n in group if n.hand == "L"]
        if R_pitches:
            last_R = max(R_pitches)
        if L_pitches:
            last_L = min(L_pitches)


# ---------------------------------------------------------------------------
# Doigtés
# ---------------------------------------------------------------------------

def assign_chord_fingers(group: list[Note], hand: str) -> list[int]:
    """Retourne les doigtés d'un accord (notes triées grave→aigu), en tenant
    compte de l'écart total (span) :
      - serré (≤ quarte/quinte) : 5-3-1 / 1-3-5 (close position, textbook)
      - moyen (≤ octave)         : 5-2-1 / 1-2-5 (le 2 ouvre mieux que le 3)
      - large (> octave)         : doigt du milieu choisi selon sa position
    """
    n = len(group)
    pitches = [note.pitch for note in group]
    span = pitches[-1] - pitches[0]

    if n == 1:
        return [3]
    if n == 2:
        if hand == "R":
            return [1, 3] if span <= 4 else ([1, 4] if span <= 7 else [1, 5])
        return [3, 1] if span <= 4 else ([4, 1] if span <= 7 else [5, 1])
    if n == 3:
        mid_pos = (pitches[1] - pitches[0]) / max(1, span)
        if hand == "R":
            if span <= 7:
                return [1, 3, 5]
            mid = 2 if mid_pos < 0.5 else 3
            return [1, mid, 5]
        if span <= 7:
            return [5, 3, 1]
        mid = 4 if mid_pos < 0.5 else 2
        return [5, mid, 1]
    if n == 4:
        return [1, 2, 3, 5] if hand == "R" else [5, 3, 2, 1]
    if n == 5:
        return [1, 2, 3, 4, 5] if hand == "R" else [5, 4, 3, 2, 1]
    return ([1, 2, 3, 4, 5] + [5] * (n - 5)) if hand == "R" else ([5, 4, 3, 2, 1] + [1] * (n - 5))


def finger_in_position(pitch: int, thumb_pos: int, hand: str) -> int | None:
    """Retourne le doigt 1-5 pour `pitch` dans la position de main dont le pouce
    est à `thumb_pos`. Retourne None si hors de portée (= il faut décaler la main).

    Position naturelle = quinte (7 demi-tons) :
      - RH : thumb_pos (1) → thumb_pos+7 (5)
      - LH : thumb_pos (1) → thumb_pos-7 (5), thumb le plus aigu
    """
    if hand == "R":
        offset = pitch - thumb_pos
    else:
        offset = thumb_pos - pitch
    if offset == 0:
        return 1
    if 1 <= offset <= 2:
        return 2
    if 3 <= offset <= 4:
        return 3
    if offset == 5:
        return 4
    if 6 <= offset <= 7:
        return 5
    return None  # hors position → caller doit décider du décalage


def choose_solo_finger(prev_pitch: int | None, prev_finger: int | None,
                       curr_pitch: int, hand: str) -> int:
    """Choisit le doigt pour une note seule en fonction de la précédente.
    Conservé pour compatibilité, mais on utilise désormais finger_in_position
    avec un suivi de position de main dans assign_fingerings.
    """
    if prev_pitch is None or prev_finger is None:
        return 3  # médius par défaut sur première note

    interval = curr_pitch - prev_pitch  # >0 = monte (vers l'aigu)
    # Pour la MG, monter vers l'aigu = aller vers le pouce → on inverse pour
    # raisonner en "direction d'augmentation des numéros de doigt".
    if hand == "L":
        interval = -interval

    if interval == 0:
        return prev_finger
    abs_int = abs(interval)
    direction = 1 if interval > 0 else -1

    # Petit pas (≤ M2) : doigt adjacent
    if abs_int <= 2:
        cand = prev_finger + direction
        if 1 <= cand <= 5:
            return cand
        # Bord : passage de pouce ou de l'auriculaire
        return 1 if direction > 0 else 5

    # Tierce-ish : sauter un doigt
    if abs_int <= 4:
        cand = prev_finger + 2 * direction
        if 1 <= cand <= 5:
            return cand
        return 1 if direction > 0 else 5

    # Quinte-ish (5–7 demi-tons) : étendre la main 1↔5 ou passage de pouce
    if abs_int <= 7:
        if direction > 0:
            return 5 if prev_finger == 1 else 1  # ouvre la main ou passe le pouce
        return 1 if prev_finger == 5 else 5

    # Grand saut : déplacement complet, pouce comme point d'appui
    return 1


def assign_fingerings(hand_notes: list[Note], hand: str, tolerance_ticks: int) -> None:
    """Annote .finger sur chaque note d'une main, par suivi de position de main.

    Principe pianistique : la main occupe une position de 5 touches (~ une quinte).
    Chaque note dans cette fenêtre prend un doigt fixe (offset → finger 1..5).
    Quand une note sort de la fenêtre, on décale la main.

    Évite le bug "pouce partout" de l'ancien algo qui raisonnait sur les
    intervalles seuls sans état de position.
    """
    onsets = group_onsets(hand_notes, tolerance_ticks)
    if not onsets:
        return

    # Position de main = pitch où se trouve le pouce.
    # RH : pouce = note la plus grave de la fenêtre
    # LH : pouce = note la plus aiguë
    thumb_pos: int | None = None

    for group in onsets:
        group.sort(key=lambda n: n.pitch)

        if len(group) > 1:
            # Accord : doigts depuis assign_chord_fingers. Recale la position
            # de main sur le pouce de l'accord.
            fingers = assign_chord_fingers(group, hand)
            for n, f in zip(group, fingers):
                n.finger = f
            if hand == "R":
                thumb_pos = group[0].pitch     # pouce sur la plus grave
            else:
                thumb_pos = group[-1].pitch    # pouce sur la plus aiguë
            continue

        # Note seule
        n = group[0]
        if thumb_pos is None:
            # 1ère note : pose le médius dessus → pouce à -4 (RH) ou +4 (LH)
            n.finger = 3
            thumb_pos = n.pitch - 4 if hand == "R" else n.pitch + 4
            continue

        f = finger_in_position(n.pitch, thumb_pos, hand)
        if f is not None:
            n.finger = f
            continue

        # Hors fenêtre → décale la main. On choisit le bord (pouce ou pinky)
        # le plus proche de la note pour minimiser le mouvement.
        if hand == "R":
            if n.pitch < thumb_pos:
                # En dessous : pose le pouce sur la note
                thumb_pos = n.pitch
                n.finger = 1
            else:
                # Au-dessus : pose le pinky sur la note
                thumb_pos = n.pitch - 7
                n.finger = 5
        else:  # LH
            if n.pitch > thumb_pos:
                thumb_pos = n.pitch
                n.finger = 1
            else:
                thumb_pos = n.pitch + 7
                n.finger = 5


# ---------------------------------------------------------------------------
# Écriture
# ---------------------------------------------------------------------------

def _hand_track_events(hand_notes: list[Note], tolerance_ticks: int) -> list[tuple[int, int, str, tuple]]:
    """Construit la liste (tick, sort_key, type, payload) ordonnée d'une piste.

    Ordre au sein d'un même tick :
      note_off (-1) avant tout, puis pour chaque note de l'accord : i.
    L'ordre physique grave→aigu est conservé pour les note_on simultanés —
    c'est cet ordre que Synthesia utilisera pour matcher la string FingerHints.
    """
    onsets = group_onsets(hand_notes, tolerance_ticks)
    events: list[tuple[int, int, str, tuple]] = []
    for onset in onsets:
        onset.sort(key=lambda n: n.pitch)
        for i, n in enumerate(onset):
            events.append((n.start_tick, i, "note_on", (n.pitch, n.velocity)))
            events.append((n.end_tick, -1, "note_off", (n.pitch,)))
    events.sort(key=lambda e: (e[0], e[1]))
    return events


def write_midi(mid_in: mido.MidiFile, notes: list[Note], output_path: Path,
               tolerance_ticks: int) -> tuple[list[Note], list[Note]]:
    """Écrit le MIDI à 3 pistes (Tempo Map, Right Hand, Left Hand).

    Retourne les listes ordonnées (R_notes, L_notes) telles qu'écrites dans
    leurs pistes respectives — utile pour construire ensuite la string
    FingerHints dans le même ordre physique.
    """
    mid_out = mido.MidiFile(ticks_per_beat=mid_in.ticks_per_beat)

    meta_events: list[tuple[int, mido.MetaMessage]] = []
    for track in mid_in.tracks:
        abs_tick = 0
        for msg in track:
            abs_tick += msg.time
            if msg.type in ("set_tempo", "time_signature", "key_signature"):
                meta_events.append((abs_tick, msg))
    meta_events.sort(key=lambda x: x[0])

    meta_track = mido.MidiTrack()
    meta_track.append(mido.MetaMessage("track_name", name="Tempo Map", time=0))
    prev_tick = 0
    for tick, msg in meta_events:
        meta_track.append(msg.copy(time=tick - prev_tick))
        prev_tick = tick
    meta_track.append(mido.MetaMessage("end_of_track", time=0))
    mid_out.tracks.append(meta_track)

    ordered_per_hand: dict[str, list[Note]] = {"R": [], "L": []}
    for hand_label, track_name in [("R", "Right Hand"), ("L", "Left Hand")]:
        track = mido.MidiTrack()
        track.append(mido.MetaMessage("track_name", name=track_name, time=0))
        track.append(mido.Message("program_change", program=0, channel=0, time=0))

        hand_notes = sorted(
            [n for n in notes if n.hand == hand_label],
            key=lambda n: (n.start_tick, n.pitch),
        )
        events = _hand_track_events(hand_notes, tolerance_ticks)

        prev_tick = 0
        for tick, _, etype, payload in events:
            delta = tick - prev_tick
            if etype == "note_on":
                pitch, vel = payload
                track.append(mido.Message("note_on", note=pitch, velocity=vel, channel=0, time=delta))
                # Conserve l'ordre physique des note_on (= ordre attendu par FingerHints)
                # On retrouve l'objet Note par (pitch, start_tick).
                for n in hand_notes:
                    if n.pitch == pitch and n.start_tick == tick and n not in ordered_per_hand[hand_label]:
                        ordered_per_hand[hand_label].append(n)
                        break
            elif etype == "note_off":
                (pitch,) = payload
                track.append(mido.Message("note_off", note=pitch, velocity=0, channel=0, time=delta))
            prev_tick = tick

        track.append(mido.MetaMessage("end_of_track", time=0))
        mid_out.tracks.append(track)

    mid_out.save(output_path)
    return ordered_per_hand["R"], ordered_per_hand["L"]


# ---------------------------------------------------------------------------
# Fichier compagnon .synthesia
# ---------------------------------------------------------------------------

# Mapping doigt → caractère dans la string FingerHints
# LH : 1..5 → "1".."5"     RH : 1..5 → "6","7","8","9","0"
_RH_CHAR = {1: "6", 2: "7", 3: "8", 4: "9", 5: "0"}


def finger_to_char(finger: int | None, hand: str) -> str:
    if finger is None:
        return "-"
    if hand == "L":
        return str(finger)
    return _RH_CHAR[finger]


def build_finger_hints(R_ordered: list[Note], L_ordered: list[Note]) -> str:
    """Construit la string FingerHints au format Synthesia.

    Notre MIDI a 3 pistes : 0=Tempo Map (sans notes), 1=Right Hand, 2=Left Hand.
    Synthesia indexe les pistes en zero-based, donc t1: et t2:.
    """
    rh = "".join(finger_to_char(n.finger, "R") for n in R_ordered)
    lh = "".join(finger_to_char(n.finger, "L") for n in L_ordered)
    parts = []
    if rh:
        parts.append(f"t1: {rh}")
    if lh:
        parts.append(f"t2: {lh}")
    return " ".join(parts)


def compute_unique_id(midi_path: Path) -> str:
    """UniqueId = MD5 hex lowercase des bytes du MIDI.

    Le wiki Synthesia dit "base-64 encoded MD5 hash" mais le code source officiel
    de metadata-editor (FileExtensions.cs:Md5sum) utilise BitConverter.ToString
    + ToLower → 32 caractères hex en minuscules. C'est ce que Synthesia attend.
    """
    return hashlib.md5(midi_path.read_bytes()).hexdigest()


def write_synthesia_xml(xml_path: Path, unique_id: str, title: str,
                        parts: str, finger_hints: str) -> None:
    root = ET.Element("SynthesiaMetadata", Version="1")
    songs = ET.SubElement(root, "Songs")
    attrs = {"Version": "1", "UniqueId": unique_id, "Title": title}
    if parts:
        attrs["Parts"] = parts
    if finger_hints:
        attrs["FingerHints"] = finger_hints
    ET.SubElement(songs, "Song", attrs)

    ET.indent(root, space="  ")
    xml_bytes = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    xml_path.write_bytes(xml_bytes + b"\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Sépare les mains et annote les doigtés d'un MIDI pour Synthesia."
    )
    ap.add_argument("input", help="Fichier MIDI d'entrée")
    ap.add_argument("-o", "--output", help="Fichier MIDI de sortie (défaut: <input>.annotated.mid)")
    ap.add_argument("--no-fingering", action="store_true", help="Ne pas calculer les doigtés")
    ap.add_argument("--pivot", type=int, default=MIDDLE_C,
                    help="Note pivot entre les mains (défaut: 60 = Do central)")
    ap.add_argument("--chord-window-ms", type=int, default=30,
                    help="Fenêtre (ms) pour considérer des notes simultanées (défaut: 30)")
    ap.add_argument("--force-resplit", action="store_true",
                    help="Force la re-séparation par registre même si le MIDI a 2 pistes")
    args = ap.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".annotated.mid")

    mid = mido.MidiFile(input_path)
    print(f"→ Lecture : {input_path}")
    print(f"  ticks/beat={mid.ticks_per_beat}  pistes={len(mid.tracks)}")

    # Conversion grossière de la fenêtre ms en ticks (on assume 500ms/beat = 120 BPM)
    tolerance_ticks = max(1, int(mid.ticks_per_beat * args.chord_window_ms / 500))

    per_track = extract_notes_per_track(mid)
    notes = [n for _, ns in per_track for n in ns]
    notes.sort(key=lambda n: (n.start_tick, n.pitch))
    print(f"  notes extraites : {len(notes)}  (sur {len(per_track)} piste(s) avec notes)")
    if not notes:
        print("  (aucune note trouvée — rien à faire)")
        return

    # Si exactement 2 pistes ont des notes, on respecte la séparation existante :
    # la piste au registre moyen le plus haut = MD, l'autre = MG.
    if len(per_track) == 2 and not args.force_resplit:
        (_, ns_a), (_, ns_b) = per_track
        avg_a = sum(n.pitch for n in ns_a) / len(ns_a)
        avg_b = sum(n.pitch for n in ns_b) / len(ns_b)
        R_src, L_src = (ns_a, ns_b) if avg_a > avg_b else (ns_b, ns_a)
        for n in R_src:
            n.hand = "R"
        for n in L_src:
            n.hand = "L"
        print(f"  séparation : 2 pistes existantes respectées (MD pitch≈{max(avg_a, avg_b):.0f}, MG≈{min(avg_a, avg_b):.0f})")
    else:
        onsets = group_onsets(notes, tolerance_ticks)
        print(f"  onsets : {len(onsets)}")
        split_hands(onsets, pivot=args.pivot)

    nR = sum(1 for n in notes if n.hand == "R")
    nL = sum(1 for n in notes if n.hand == "L")
    print(f"  MD={nR}  MG={nL}")

    if not args.no_fingering:
        R_notes = [n for n in notes if n.hand == "R"]
        L_notes = [n for n in notes if n.hand == "L"]
        assign_fingerings(R_notes, "R", tolerance_ticks)
        assign_fingerings(L_notes, "L", tolerance_ticks)
        print("  doigtés assignés (1=pouce … 5=auriculaire)")

    R_ordered, L_ordered = write_midi(mid, notes, output_path, tolerance_ticks)
    print(f"→ MIDI       : {output_path}")

    # Fichier compagnon .synthesia
    unique_id = compute_unique_id(output_path)
    parts_str = ""
    if R_ordered:
        parts_str += "t1:RA"
    if L_ordered:
        parts_str += (" " if parts_str else "") + "t2:LA"

    finger_hints = "" if args.no_fingering else build_finger_hints(R_ordered, L_ordered)

    xml_path = output_path.with_suffix(".synthesia")
    write_synthesia_xml(xml_path, unique_id, output_path.stem, parts_str, finger_hints)
    print(f"→ .synthesia : {xml_path}")
    print(f"  UniqueId  : {unique_id}")
    print(f"  Parts     : {parts_str}")
    if finger_hints:
        preview = finger_hints if len(finger_hints) <= 80 else finger_hints[:77] + "..."
        print(f"  FingerHints: {preview}")


if __name__ == "__main__":
    main()
