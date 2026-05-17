# midi-ui

Outils pour transformer une bibliothèque MIDI en versions jouables sur Synthesia (mains séparées, doigtés, sections musicales, version humanisée) + **Drum Trainer**, app web type Synthesia pour apprendre la batterie sur un Yamaha DD-75.

## 🎹 Côté piano / Synthesia

Pipeline Python qui prend un dossier de MIDI bruts et produit pour chaque morceau :
- 1 MIDI à 3 pistes (Tempo Map + Right Hand + Left Hand) avec doigtés
- 1 fichier compagnon `.synthesia` (XML) que Synthesia lit
- Si > 1m30 : sous-dossier de "parts" découpées par sections musicales détectées
- Version humanisée (vélocité, timing, pédale, rubato)

### Scripts

| Fichier | Rôle |
|---|---|
| `annotate_midi.py` | Annote UN MIDI : sépare mains, assigne doigtés (position-aware), génère le `.synthesia` |
| `batch_annotate.py` | Boucle sur tout le dossier `midi/`, détecte les sections musicales (matrice de similarité + détection de nouveauté Foote), humanise chaque MIDI |
| `detect_sections.py` | Algo MIR de découpe en sections (intro/couplet/refrain/outro) |
| `humanize.py` | Variation humaine : vélocité jittered + emphase temps forts + voix de tête, timing ±10ms, étalement d'accord, articulation legato/staccato, pédale syncopée, rubato |
| `rename_midis.py` | Renomme en `[Style] Artiste - Chanson (année, durée).mid` + bouge les infos de source/arrangement dans le `Subtitle` du `.synthesia` |
| `rename_parts_compact.py` | Compacte les noms des parts au format `[Style] Artiste - Chanson (Part N, année, durée).mid` |
| `fix_titles.py` | Écrit l'attribut `Title` dans les `.synthesia` pour qu'il colle au filename |
| `inspect_midi.py` | Affiche le contenu d'un MIDI annoté de façon lisible |

### Quick start piano

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# Mettre des .mid dans midi/ ou midi/more/
.venv/bin/python batch_annotate.py     # annotation + humanisation (~5 min sur 380 fichiers)
.venv/bin/python rename_midis.py       # renommage propre
.venv/bin/python rename_parts_compact.py
.venv/bin/python fix_titles.py
# Sortie : midi/annotated/
```

### Format Synthesia

Documenté dans `memory/reference_synthesia_format.md` (non versionné). Faits clés :
- `UniqueId` du `.synthesia` = **MD5 hex lowercase** des bytes du `.mid` (pas base64 comme dit le wiki)
- `Parts` = `t1:RA t2:LA` (track 1 = right hand all, track 2 = left hand all)
- `FingerHints` = string unique, **1-5 = MG, 6-9-0 = MD** (6=pouce R, 0=pinky R)

## 🥁 Drum Trainer

App web type Synthesia pour apprendre la batterie, pensée pour enfants 4-6 ans. Compatible Yamaha DD-75 via Web MIDI API.

| Fichier | Rôle |
|---|---|
| `drum-trainer/kids.html` | App version enfants (mascotte Boumbi, écrans accueil/libre/apprendre/progrès, dispo physique DD-75 en Mode Libre) |
| `drum-trainer/index.html` | App version debug (calibration, log MIDI temps réel, mode Demo) |
| `drum-trainer/DD-75-reference.md` | Référence complète du DD-75 : 75 kits, mapping notes MIDI, drum map, dispo physique des pads |
| `drum-trainer/PRD-kids.md` | Product Requirements Document de la version kids |
| `drum-trainer/PRD-next-exos.md` | Specs détaillées des 4 prochains modes à coder (Runner, Mémo, Echo, Studio) |

### Quick start drum trainer

```bash
cd drum-trainer && python3 -m http.server 8765
```

Ouvrir **http://localhost:8765/kids.html** dans Chrome (Web MIDI non supporté sur Safari).

### DD-75 — info essentielle

Le DD-75 **ne transmet PAS de Program Change** quand on change de kit. Le mapping notes par défaut de mon app correspond au **Kit 1 (Maple Kit 1)** :

| Pad / Pédale | Voix | Note MIDI |
|---|---|---|
| Pedal 1 (Kick, droite) | Maple Bass Drum 3 | 36 |
| Pedal 2 (HH foot, gauche) | Hi-Hat Pedal Bright | 44 |
| Pad 1 (Snare) | Maple Snare Open Rim | **40** ← pas 38 GM |
| Pad 2 (Tom L) | Maple Tom 5 | 48 |
| Pad 3 (Tom M) | Maple Tom 4 | 47 |
| Pad 4 (Tom H) | Maple Tom 2 | 43 |
| Pad 5 (Crash) | Crash Cymbal Dark | 57 |
| Pad 6 (Hi-Hat) | Hi-Hat Closed Bright | 42 |
| Pad 7 (Ride Cup) | Ride Cymbal Cup Warm | 53 |
| Pad 8 (Ride) | Ride Cymbal Warm 1 | 51 |

Si tu utilises un autre kit, calibre via le bouton 🎯 sur l'accueil.

## Licence

MIT — fais-en ce que tu veux. Les MIDI dans `midi/` (non versionnés) restent la propriété de leurs ayants droits respectifs.
