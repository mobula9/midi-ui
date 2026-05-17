"""Affiche le contenu d'un MIDI annoté : noms de pistes, notes, doigtés."""
import sys
import mido

mid = mido.MidiFile(sys.argv[1])
print(f"=== {sys.argv[1]} ===")
print(f"ticks_per_beat: {mid.ticks_per_beat}, pistes: {len(mid.tracks)}\n")

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
def name(p): return f"{PITCH_NAMES[p % 12]}{p // 12 - 1}"

for i, track in enumerate(mid.tracks):
    print(f"--- Track {i}: {track.name!r} ({len(track)} events) ---")
    abs_tick = 0
    last_text = None
    for msg in track:
        abs_tick += msg.time
        if msg.type == "track_name":
            print(f"  [name]  {msg.name!r}")
        elif msg.type == "set_tempo":
            print(f"  t={abs_tick:>5}  tempo={mido.tempo2bpm(msg.tempo):.0f} BPM")
        elif msg.type == "time_signature":
            print(f"  t={abs_tick:>5}  {msg.numerator}/{msg.denominator}")
        elif msg.type == "text":
            last_text = msg.text
            print(f"  t={abs_tick:>5}  [doigté={msg.text}]")
        elif msg.type == "note_on" and msg.velocity > 0:
            tag = f"  ← doigt {last_text}" if last_text else ""
            print(f"  t={abs_tick:>5}  ON  {name(msg.note):>4} (vel={msg.velocity}){tag}")
            last_text = None
        elif msg.type in ("note_off",) or (msg.type == "note_on" and msg.velocity == 0):
            pass  # skip note_off for readability
    print()
