# Yamaha DD-75 — Référence MIDI & Kits

Documentation extraite de :
- [DD-75 Owner's Manual](https://data.yamaha.com/files/download/other_assets/9/892349/DD-75_owners_manual_En_E0_ZW55120.pdf)
- [DD-75 MIDI Reference](https://data.yamaha.com/files/download/other_assets/3/892623/dd75_en_mr_a0_web.pdf)

---

## 1. Comportement MIDI à connaître

| Spec | Valeur |
|---|---|
| Canal MIDI transmis (par défaut) | **10** (canal des drums, indices 0-based : 9) |
| Canaux MIDI reçus | 1–16 (multi-timbre) |
| `Note Off` transmis sous forme | `Note On` avec velocity = 0 |
| Vélocité transmise | 1–127 (sensible au toucher) |
| **Program Change transmis** | ❌ **NON** (le DD-75 ne signale PAS le changement de kit) |
| Bank Select (CC 0/32) transmis | ❌ NON |
| Pitch Bend / Aftertouch | ❌ NON |
| Active Sense, Clock, System Real Time | ✓ OUI |

→ **Conséquence importante** : impossible de détecter côté logiciel quel kit l'utilisateur a sélectionné sur le DD-75. Si tu changes de kit, les numéros de note envoyés changent aussi (chaque kit a des assignations de voix différentes), et l'app ne peut pas le savoir. Solution : fixer le DD-75 sur **Kit 1 (Maple Kit 1)** pour rester sur le mapping par défaut, ou faire une calibration manuelle dans l'app.

### `MIDI Note Number Auto Selection`

Paramètre du DD-75, **ON par défaut**. Quand ON, chaque pad envoie le numéro de note correspondant à la **voix actuellement assignée** dans le drum map. Quand OFF, chaque pad envoie un numéro de note arbitraire qu'on a choisi manuellement.

À garder **ON** dans la pratique : laisse le DD-75 envoyer les bonnes notes en fonction du kit sélectionné.

---

## 2. Disposition physique des 8 pads + 2 pédales

Vue de face du DD-75 (telle qu'on la voit sur l'engin) :

```
       ┌─────┐                                    ┌─────┐
       │  5  │                                    │  7  │
       │CRASH│                                    │RIDE │
       │     │                                    │ CUP │
       └─────┘         ┌───┐ ┌───┐                └─────┘
                       │ 2 │ │ 3 │
                       │TOM│ │TOM│
                       │ L │ │ M │
       ┌─────┐         └───┘ └───┘                ┌─────┐
       │  6  │                                    │  8  │
       │HI-  │                                    │RIDE │
       │HAT  │         ┌───┐ ┌───┐                │     │
       │     │         │ 1 │ │ 4 │                │     │
       └─────┘         │SN.│ │TOM│                └─────┘
                       │   │ │ H │
                       └───┘ └───┘

  ┌─────┐                                              ┌─────┐
  │PEDAL│                                              │PEDAL│
  │  2  │                                              │  1  │
  │ HH  │                                              │KICK │
  │FOOT │                                              │     │
  └─────┘                                              └─────┘
```

- **Pad 5** (cymbale haut gauche) — généralement Crash
- **Pad 7** (cymbale haut droit) — généralement Ride Cup
- **Pads 2 + 3** (toms hauts au centre) — Toms moyens
- **Pad 6** (mid gauche) — Hi-Hat fermé
- **Pad 8** (mid droit) — Ride
- **Pads 1 + 4** (centre bas) — Snare + Tom grave
- **Pédale 2** (gauche) — Hi-Hat foot (close)
- **Pédale 1** (droite) — Kick (sensible au toucher)

### Astuce hi-hat ouvert/fermé (Kit 1)

> Frapper **Pad 6** + tenir **Pédale 2** = Hi-Hat fermé
> Frapper **Pad 6** sans pédale = Hi-Hat ouvert
> Appuyer **Pédale 2** seule = Hi-Hat pedal sound

---

## 3. Notes MIDI envoyées par défaut (Kit 1 — Maple Kit 1)

Les notes MIDI sortantes dépendent du kit. Pour le Kit 1, voici la table (issue du croisement entre la liste des kits et le drum map) :

| Pad / Pédale | Voix assignée | Note MIDI | Note |
|---|---|---|---|
| **Pedal 1** (Kick) | 3 — Maple Bass Drum 3 | **36** | C1 |
| **Pedal 2** (HH foot) | 180 — Hi-Hat Pedal Bright | **44** | G#1 |
| **Pad 1** (Snare) | 40 — Maple Snare Open Rim | **40** | E1 |
| **Pad 2** (Tom L) | 102 — Maple Tom 5 | **48** | C2 |
| **Pad 3** (Tom M) | 103 — Maple Tom 4 | **47** | B1 |
| **Pad 4** (Tom H) | 105 — Maple Tom 2 | **43** | G1 |
| **Pad 5** (Crash) | 211 — Crash Cymbal Dark | **57** | A2 |
| **Pad 6** (Hi-Hat) | 179 — Hi-Hat Closed Bright | **42** | F#1 |
| **Pad 7** (Ride Cup) | 210 — Ride Cymbal Cup Warm | **53** | F2 |
| **Pad 8** (Ride) | 208 — Ride Cymbal Warm 1 | **51** | D#2 |

**Remarque** : la snare du DD-75 envoie note **40** (Snare Tight position du GM drum map), pas note **38** (Snare standard du GM). C'est pour ça que le mapping GM par défaut de mes apps **rate la snare**. Mon mapping doit utiliser ces vraies valeurs.

---

## 4. Liste complète des 75 kits

Source : DD-75 Owner's Manual, p. 48-50.

| Kit # | Nom | Pedal 1 (Kick) | Pedal 2 (HH) | Pad 1 (Snare) | Pad 2 | Pad 3 |
|---|---|---|---|---|---|---|
| 1 | Maple Kit 1 | Maple Bass Drum 3 | HH Pedal Bright | Maple Snare Open Rim | Maple Tom 5 | Maple Tom 4 |
| 2 | Maple Kit 2 | Maple Bass Drum 3 | HH Pedal Bright | Maple Snare Open Rim | Maple Tom 5 | Maple Tom 4 |
| 3 | Maple Kit 3 | Maple Bass Drum 3 | HH Pedal Bright | Maple Snare Open Rim | Maple Tom 5 | Ride Cymbal Warm 1 |
| 4 | Maple Kit 4 | Maple Bass Drum 3 | HH Pedal Bright | Maple Snare Head | Maple Tom 4 | Maple Tom 2 |
| 5 | Oak Kit 1 | Oak Bass Drum | HH Pedal Dark | Oak Snare Open Rim | Oak Tom 5 | Oak Tom 4 |
| 6 | Oak Kit 2 | Oak Bass Drum | HH Pedal Dark | Oak Snare Open Rim | Oak Tom 5 | Oak Tom 4 |
| 7 | Oak Kit 3 | Oak Bass Drum | HH Pedal Dark | Oak Snare Open Rim | Oak Tom 5 | Ride Cymbal Bright |
| 8 | Oak Kit 4 | Oak Bass Drum | HH Pedal Dark | Oak Snare Head | Oak Tom 5 | Oak Tom 2 |
| 9 | Hard Rock Kit 1 | Bass Drum Rock 3 | HH Pedal Dark 2 | Snare Open Rim Hard Rock | Tom Hard Rock 5 | Tom Hard Rock 4 |
| 10 | Hard Rock Kit 2 | Bass Drum Close Power | HH Pedal Power | Snare Head Hard Rock | Tom Hard Rock 4 | Ride Cymbal Warm 3 |
| 11 | Hard Rock Kit 3 | Bass Drum Ambient+ | HH Pedal Power | Snare Open Rim Hard Rock | Tom Hard Rock 5 | Tom Hard Rock 4 |
| 12 | Hard Rock Kit 4 | Bass Drum Rock | HH Pedal | Snare Rock Rim | Tom Rock 6 | Tom Rock 4 |
| 13 | Hard Rock Kit 5 | Bass Drum Rock | HH Pedal | Snare Rock | Tom Room 5 | Tom Room 3 |
| 14 | Analog T8 Kit 1 | Kick T8 4 | HH Pedal T8 | Snare T8 6 | Tom T8 6 | Tom T8 3 |
| 15 | Analog T8 Kit 2 | Kick Slimy | HH Pedal T8 | Snare Clap Analog | Tom T8 7 | Tom T8 4 |
| 16 | Analog T8 Kit 3 | Kick T8 1 | HH Pedal T8 | Snare T8 3 | Conga T8 3 | Conga T8 2 |
| 17 | Vox Kit | Bass Drum Vox 1 | HH Pedal Vox | Snare Vox Open Rim | Tom Vox 3 | Tom Vox 2 |
| 18 | Stereo Kit 1 | Bass Drum Close Power | HH Pedal Power | Snare Power | Tom Power 6 | Tom Power 4 |
| 19 | Stereo Kit 2 | Bass Drum Open Power | HH Pedal Power | Snare Power 2 | Tom Power 5 | Tom Power 3 |
| 20 | Stereo Kit 3 | Bass Drum Ambient+ | HH Pedal Power | Snare Rough 2 | Tom Power 6 | Tom Power 4 |
| 21 | Stereo Kit 4 | Bass Drum Ambient+ | HH Pedal Power | Snare Soft Power | Tom Power 4 | Tom Power 2 |
| 22 | Stereo Kit 5 | Bass Drum Close Power | HH Pedal Power | Snare Rough | Tom Power 6 | Tom Power 4 |
| 23 | Stereo Ballad Kit | Bass Drum Ambient+ | HH Pedal Power | Snare Power | Tom Power 5 | Tom Power 3 |
| 24 | Ballad Kit 1 | Bass Drum | HH Pedal | Snare | Mid Tom L | Floor Tom H |
| 25 | Ballad Kit 2 | Bass Drum 2 | HH Pedal | Snare Soft 2 | Mid Tom L | Floor Tom H |
| 26 | Analog Ballad Kit 1 | Bass Drum Analog H | HH Closed Analog 2 | Snare Analog 1 | Tom Analog 6 | Tom Analog 4 |
| 27 | Analog Ballad Kit 2 | Bass Drum Analog L | HH Closed Analog 2 | Snare Analog 1 | Tom Analog 6 | Tom Analog 4 |
| 28 | Stereo Shuffle Kit 1 | Bass Drum Open Power | HH Pedal Power | Snare Rough | Tom Power 6 | Tom Power 4 |
| 29 | Stereo Shuffle Kit 2 | Bass Drum Close Power | HH Pedal Power | Snare Rough 2 | Tom Power 6 | Tom Power 4 |
| 30 | Stereo Shuffle Kit 3 | Bass Drum Close Power | HH Pedal Power | Snare Rough 2 | Tom Power 6 | Tom Power 4 |
| 31 | Stereo Slow Rock Kit | Bass Drum Close Power | HH Pedal Power | Snare Soft Power | Tom Power 6 | Tom Power 4 |
| 32 | Electric Kit 1 | Bass Drum Gate | HH Pedal | Snare Noisy 2 | Tom Electronic 6 | Tom Electronic 4 |
| 33 | Electric Kit 2 | Bass Drum Gate | HH Pedal | Snare Snappy Electronic | Tom Electronic 6 | Tom Electronic 4 |
| 34 | Dance Kit 1 | Kick Techno L | HH Closed Analog 4 | Snare Clap | Tom Analog 6 | Tom Analog 4 |
| 35 | Dance Kit 2 | Kick Techno | HH Closed Analog 4 | Snare Techno | Tom Analog 6 | Tom Analog 4 |
| 36 | Analog Kit | Bass Drum Analog H | HH Closed Analog 2 | Snare Analog 1 | Hand Clap | Tom Analog 4 |
| 37 | DJ Kit | Kick Techno Q | HH Closed Analog 4 | Rim Gate | Yo! | Go! |
| 38 | Disco Kit 1 | Bass Drum | HH Pedal | Snare Tight | Mid Tom H | Low Tom |
| 39 | Disco Kit 2 | Kick Techno L | HH Closed Analog 4 | Snare Techno | Hand Clap | Tom Analog 4 |
| 40 | Jazz Kit | Bass Drum Jazz | HH Pedal | Snare Jazz L | Tom Jazz 6 | Tom Jazz 4 |
| 41 | Brush Kit | Bass Drum Hard | HH Pedal | Brush Slap | Tom Brush 6 | Tom Brush 4 |
| 42 | 5/4 Jazz Kit | Bass Drum Soft | HH Pedal | Snare Soft 2 | High Tom | Mid Tom L |
| 43 | Dixieland Kit | Bass Drum Hard | HH Pedal | Snare Soft 2 | Brush Tap | Brush Slap |
| 44 | Soul Kit | Bass Drum Open Power | HH Pedal Power | Snare Rough 2 | Tom Power 5 | Tom Power 3 |
| 45 | R & R Kit | Bass Drum | HH Pedal | Snare Soft | High Tom | Mid Tom L |
| 46 | 6/8 Blues Kit | Bass Drum Ambient+ | HH Pedal Power | Snare Soft Power | Tom Power 5 | Tom Power 3 |
| 47 | Country Kit | Bass Drum | HH Pedal | Snare Room L | Tom Room 4 | Tom Room 2 |
| 48 | Samba Kit | Bass Drum | Maracas | Cuica Mute | Agogo H | Agogo L |
| 49 | Bossa Nova Kit 1 | Bass Drum Hard | HH Pedal | Side Stick | Tom Brush 5 | Tom Brush 3 |
| 50 | Bossa Nova Kit 2 | Oak Bass Drum | HH Pedal Dark | Oak Snare Head | Oak Tom 5 | Oak Tom 2 |
| 51 | Conga Kit | Conga L Slide | Cowbell Top | Conga H Slap Mute | Conga H Open | Conga L Open |
| 52 | Conga & Bongo Kit 1 | Bass Drum 2 | Cowbell Top | Conga H Open | Conga L Open | Bongo Finger H Open 1 |
| 53 | Conga & Bongo Kit 2 | Bass Drum 2 | Cowbell Top | Conga 2 H Open | Conga 2 L Open | Bongo 2 H Mute |
| 54 | Salsa Kit | Bass Drum | Wood Block H | Bongo L Open 3 Fingers | Timbale L Open | Timbale H Open |
| 55 | Beguine Kit | Bass Drum Hard | HH Pedal | Side Stick | Mid Tom H | Low Tom |
| 56 | Reggae Kit | Bass Drum Ambient+ | HH Pedal Power | Snare Rough | Timbale L Open | Timbale H Open |
| 57 | Waltz Kit | Bass Drum Jazz | HH Pedal | Brush Tap | Brush Slap | Tom Brush 5 |
| 58 | March Kit | Gran Cassa | HH Pedal | Band Snare 1 | Wood Block H | Wood Block L |
| 59 | Timpani Kit | Gran Cassa | HH Pedal | Timpani E1 | Timpani A1 | Timpani D2 |
| 60 | Arabic Kit 1 | Katem Dom | Katem Tak 1 | Tablah Dom 1 | Tablah Sak 1 | Tablah Tak 4 |
| 61 | Arabic Kit 2 | Katem Dom | Katem Tak 1 | Daholla Dom | Daholla Sak 1 | Daholla Tak 2 |
| 62 | Arabic Kit 3 | Sagat 1 | Sagat 3 | Katem Dom | Katem Sak 1 | Katem Tak 1 |
| 63 | Brazil Kit 1 | Tan Tan 1 Open RH | Tan Tan 1 Closed RH | Pandeiro L Thumb Closed | Pandeiro L Toe Rim | Pandeiro L Heel |
| 64 | Brazil Kit 2 | Surdo 2 Open | Surdo 2 Mute | Pandeiro L Thumb Closed | Pandeiro L Toe Rim | Pandeiro L Heel |
| 65 | Brazil Kit 3 | Zabumba Open RH | Zabumba Mute RH | Pandeiro L Thumb Closed | Pandeiro L Toe Rim | Pandeiro L Heel |
| 66 | Indian Kit 1 | Dholak 2 Rim 1 | Hatheli Short | Baya ghe | Baya ge | Tabla na |
| 67 | Indian Kit 2 | Dhol 2 Open | Dhol 2 Rim | Dholak 2 Open | Dholak 2 Rim 1 | Dholak 2 Rim 2 |
| 68 | Indian Kit 3 | Dafli Open | Dafli Rim | Dhol 2 Open | Dhol 2 Rim | Dholki H Mute |
| 69 | Indian Kit 4 | Dafli Open | Dafli Rim | Dhol 1 Open | Dhol 1 Slap | Dhol 2 Slap |
| 70 | African Kit | Bass Drum | Cabasa | Djembe Slap | Djembe L | Talking Drum Left Hand Open |
| 71 | Folklore Kit | Bass Drum | Jingle Bells | Cajon 2 Slap | Cajon 2 L | Wind Chime |
| 72 | Japanese Kit | Yaguradaiko | Yaguradaiko Rim | Oodaiko | Shimedaiko | Atarigane |
| 73 | Chinese Kit | Dagu Heavy | Zhongcha Mute | Paigu M | Bangu | Xiaocha Mute |
| 74 | SE Kit 1 | Footsteps | Footsteps | Rooster | Horse Neigh | Cow |
| 75 | SE Kit 2 | Go! | Footsteps | Yo! | Huuaah! | Uh!+Hit |

(Voir le manuel pour les voix complètes Pad 4 à Pad 8 — non listées ici par souci de concision.)

---

## 5. Drum map — voix → note MIDI (Standard Kit 1)

Les voix les plus courantes et leur position dans le drum map :

| Note MIDI | Note nom | Voix Standard | Voix Maple Kit | Voix Oak Kit | Voix Rock Kit |
|---|---|---|---|---|---|
| 33 | A0 | Bass Drum Soft | Maple Bass Drum 1 | Maple Bass Drum 1 | – |
| 35 | B0 | Bass Drum Hard | Maple Bass Drum 2 | Maple Bass Drum 2 | Bass Drum H |
| **36** | C1 | Bass Drum | **Maple Bass Drum 3** | Oak Bass Drum | Bass Drum Rock |
| 37 | C#1 | Side Stick | Maple Side Stick | Oak Side Stick | – |
| 38 | D1 | Snare | Maple Snare Head | Oak Snare Head | Snare Rock |
| 39 | D#1 | Hand Clap | Hand Clap 2 | – | – |
| **40** | E1 | Snare Tight | **Maple Snare Open Rim** | Oak Snare Open Rim | Snare Rock Rim |
| 41 | F1 | Floor Tom L | Maple Tom 1 | Oak Tom 1 | Tom Rock 1 |
| **42** | F#1 | Hi-Hat Closed | **Hi-Hat Closed Bright** | Hi-Hat Closed Dark | – |
| 43 | G1 | Floor Tom H | **Maple Tom 2** | Oak Tom 2 | Tom Rock 2 |
| **44** | G#1 | Hi-Hat Pedal | **Hi-Hat Pedal Bright** | Hi-Hat Pedal Dark | – |
| 45 | A1 | Low Tom | Maple Tom 3 | Oak Tom 3 | Tom Rock 3 |
| 46 | A#1 | Hi-Hat Open | Hi-Hat Open Bright | Hi-Hat Open Dark | – |
| **47** | B1 | Mid Tom L | **Maple Tom 4** | Oak Tom 4 | Tom Rock 4 |
| **48** | C2 | Mid Tom H | **Maple Tom 5** | Oak Tom 5 | Tom Rock 5 |
| 49 | C#2 | Crash Cymbal 1 | Crash Cymbal Warm | Crash Cymbal Bright | – |
| 50 | D2 | High Tom | Maple Tom 6 | Oak Tom 6 | Tom Rock 6 |
| **51** | D#2 | Ride Cymbal 1 | **Ride Cymbal Warm 1** | Ride Cymbal Bright | – |
| 52 | E2 | Chinese Cymbal | Chinese Cymbal 2 | Chinese Cymbal 2 | – |
| **53** | F2 | Ride Cymbal Cup | **Ride Cymbal Cup Warm** | Ride Cymbal Cup Bright | – |
| 54 | F#2 | Tambourine | – | – | – |
| 55 | G2 | Splash Cymbal | Splash Cymbal 2 | Splash Cymbal 2 | – |
| 56 | G#2 | Cowbell | – | – | – |
| **57** | A2 | Crash Cymbal 2 | **Crash Cymbal Dark** | Crash Cymbal Dark 2 | – |
| 59 | B2 | Ride Cymbal 2 | Ride Cymbal Warm 2 | Ride Cymbal Warm 2 | – |

Notes en **gras** : utilisées par Maple Kit 1 (le kit par défaut sur lequel l'app `drum-trainer/kids.html` est calibrée).

---

## 6. Mapping recommandé pour mes apps

Mes apps doivent utiliser les notes du Kit 1 (Maple Kit 1) par défaut :

```js
const DD75_KIT1_NOTES = {
  kick:    36,  // Pedal 1 — Maple Bass Drum 3
  hhpedal: 44,  // Pedal 2 — Hi-Hat Pedal Bright
  snare:   40,  // Pad 1   — Maple Snare Open Rim
  tomL:    48,  // Pad 2   — Maple Tom 5
  tomM:    47,  // Pad 3   — Maple Tom 4
  tomH:    43,  // Pad 4   — Maple Tom 2
  crash:   57,  // Pad 5   — Crash Cymbal Dark
  hihat:   42,  // Pad 6   — Hi-Hat Closed Bright
  ridecup: 53,  // Pad 7   — Ride Cymbal Cup Warm
  ride:    51,  // Pad 8   — Ride Cymbal Warm 1
};
```

⚠ La snare est à **40, pas 38** comme dans le GM standard. C'est la principale différence par rapport au GM Drum Map.
