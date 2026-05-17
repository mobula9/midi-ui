"""Génère un petit MIDI de test : mélodie main droite + accords main gauche,
mais sur UNE SEULE piste, sans indication de main ni de doigté, pour vérifier
que annotate_midi.py sépare correctement et annote.
"""
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage

TPB = 480  # ticks per beat
QUARTER = TPB
HALF = TPB * 2

mid = MidiFile(ticks_per_beat=TPB)
track = MidiTrack()
mid.tracks.append(track)
track.append(MetaMessage("set_tempo", tempo=mido.bpm2tempo(100), time=0))
track.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))

# On va construire la liste d'events absolus puis convertir en deltas.
events = []  # (abs_tick, kind, note, vel)

def note(start_beat: float, dur_beats: float, pitch: int, vel: int = 80):
    s = int(start_beat * TPB)
    e = int((start_beat + dur_beats) * TPB)
    events.append((s, "on", pitch, vel))
    events.append((e, "off", pitch, 0))

# --- Mesure 1 : accord de Do (LH) + mélodie Do-Ré-Mi-Fa (RH)
for p in (48, 52, 55):  # C3 E3 G3
    note(0, 4, p, 70)
note(0, 1, 72, 90)  # C5
note(1, 1, 74, 90)  # D5
note(2, 1, 76, 90)  # E5
note(3, 1, 77, 90)  # F5

# --- Mesure 2 : accord de Sol (LH) + mélodie Sol-Mi-Ré-Do (RH)
for p in (43, 47, 50):  # G2 B2 D3
    note(4, 4, p, 70)
note(4, 1, 79, 90)  # G5
note(5, 1, 76, 90)  # E5
note(6, 1, 74, 90)  # D5
note(7, 1, 72, 90)  # C5

# --- Mesure 3 : accord de La min (LH) + arpège descendant (RH)
for p in (45, 48, 52):  # A2 C3 E3
    note(8, 4, p, 70)
note(8, 0.5, 76, 90)
note(8.5, 0.5, 74, 90)
note(9, 0.5, 72, 90)
note(9.5, 0.5, 71, 90)
note(10, 1, 72, 90)
note(11, 1, 74, 90)

# --- Mesure 4 : accord de Fa (LH) + Sol-Fa-Mi-Do (RH)
for p in (41, 45, 48):  # F2 A2 C3
    note(12, 4, p, 70)
note(12, 1, 79, 90)
note(13, 1, 77, 90)
note(14, 1, 76, 90)
note(15, 1, 72, 90)

# Trier et écrire en deltas
events.sort(key=lambda e: (e[0], 0 if e[1] == "off" else 1))
prev = 0
for abs_tick, kind, pitch, vel in events:
    delta = abs_tick - prev
    if kind == "on":
        track.append(Message("note_on", note=pitch, velocity=vel, time=delta))
    else:
        track.append(Message("note_off", note=pitch, velocity=0, time=delta))
    prev = abs_tick

track.append(MetaMessage("end_of_track", time=0))
mid.save("test_input.mid")
print("Écrit test_input.mid")
