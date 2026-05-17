# Drum Trainer — Prochains exos / modes de jeu

État au moment où ce doc est écrit : modes existants = **Libre**, **Apprendre** (drum hero), **Réflexe**, **Spotify**, **Progrès**. Ce doc décrit les **4 prochains modes** à implémenter, dans l'ordre de priorité.

Public visé : **enfants 4–6 ans** sur Yamaha DD-75 (mais clavier/clic fonctionne aussi).

Toutes les données restent **per-profile** (préfixées via `pkey('xxx')` — cf. système de profils existant).

---

## 1. 🦖 Boumbi Runner (priorité 1)

**Pitch** : Boumbi court à droite, des obstacles arrivent → tape le bon pad au bon moment pour les éviter / les détruire. Comme le dino de Chrome offline, mais c'est ta batterie qui contrôle Boumbi.

### Pourquoi
- Fun pur, hook addictif "encore un essai".
- Gameplay simple à comprendre (3 ans+ peuvent jouer le niveau 1).
- Le rythme **émerge** du jeu plutôt que d'être enseigné frontalement.
- Compatible avec les modes existants (réutilise le mapping LANES, le rendu canvas, l'audio).

### Gameplay
- Side-scroller, Boumbi à gauche de l'écran, animation de course en boucle.
- Le décor défile vers la gauche.
- Des obstacles apparaissent à droite et se déplacent vers Boumbi.
- Chaque obstacle est associé à **un pad** du DD-75. Pour le franchir, taper le pad pile quand l'obstacle arrive sur Boumbi (fenêtre de tolérance ±150ms).
- Pad correct au bon moment → obstacle **détruit**, Boumbi continue.
- Pad incorrect ou trop tôt/trop tard → Boumbi se prend l'obstacle, **−1 vie**.
- 3 vies. 0 vie → game over.

### Mapping pads ↔ obstacles (niveau cible)
| Obstacle visuel | Pad | Raison |
|---|---|---|
| 🌵 Cactus bas | Kick (pédale droite) | "Saut" — métaphore intuitive |
| 🌿 Buisson | Snare (Pad 1) | Frappe puissante au centre |
| 🪨 Caillou bas | Tom L (Pad 2) | Grave |
| 🪨 Caillou haut | Tom H (Pad 4) | Aigu |
| 🦅 Oiseau (en haut) | Crash (Pad 5) | Cymbale aiguë, métaphore "frappe en l'air" |
| ☁️ Nuage électrique | Hi-Hat (Pad 6) | Léger, frappé |

Aux premiers niveaux, on n'utilise qu'un sous-ensemble (kick seul → kick + snare → etc.).

### Progression par niveaux
Chaque niveau dure ~45–60s. La vitesse de défilement augmente progressivement.

| Niveau | Pads utilisés | Tempo (apparitions/min) | Pattern d'obstacles |
|---|---|---|---|
| 1 | kick | 60 | Tout droit, ♩ ♩ ♩ ♩ régulier |
| 2 | kick + snare | 80 | boum-tac-boum-tac alternés |
| 3 | + crash | 100 | + oiseaux entre les obstacles bas |
| 4 | + tom L | 120 | enchaînements de 3, syncopes simples |
| 5 | + hihat | 140 | doubles-croches en hi-hat |
| 6+ | tous | 160+ | pattern complet, type rock basique |

À partir du niveau 5, possibilité de **synchroniser sur un morceau Spotify** (mode "Boumbi vs ta musique") : les obstacles tombent en phase avec le BPM du morceau cached. Réutilise tout le pipeline Spotify+tap tempo existant.

### Anti-frustration (4–6 ans)
- 3 vies, pas restart immédiat sur erreur.
- Visuel d'échec doux : Boumbi fait "ouille" mais ne meurt pas, le jeu continue 1s puis reprend.
- À la mort : écran "tu as fait X mètres ! 💪" avec le meilleur score affiché.
- Pad **bonne lane mais mauvais timing** → animation "presque !" + perte de 0 vie (au lieu de pad faux).
- Pad **mauvaise lane** → −1 vie + flash rouge (comme en réflexe, existant).

### Récompenses
- **Distance en mètres** (1 obstacle franchi = 5m).
- Stars : 1⭐ à 100m, 2⭐ à 250m, 3⭐ à 500m.
- Meilleur score per-profile.
- Tous les 100m → nouveau fond se débloque (jungle, océan, espace, lune, jurassique).

### Stack technique
- **Rendu** : canvas 2D, même approche que `drawPlay`. Réutiliser `play-canvas` ou créer un nouveau `runner-canvas`.
- **Boucle** : `requestAnimationFrame`. État = `{distance, lives, obstacles[], speed, lastSpawn}`.
- **Génération d'obstacles** : à intervalles dérivés du tempo du niveau, push un obstacle avec `{x: canvas.width, lane, type, t: performance.now()}`. Position à l'écran : `x = startX - (now - t) * speed`.
- **Détection collision** : quand un obstacle entre dans la fenêtre de hit (x dans `[boumbiX - hitWindow, boumbiX + hitWindow]`), accepter le pad correspondant.
- **Hits MIDI** : route via `onMIDI` quand `currentScreen === 'runner'`. Pas de "awaitingStart" — tap sur kick = saut au début, démarre la partie.
- **Audio** : pad joue son son normal (réutilise `freePadHit` ou `playClick`-like). Pas d'audio supplémentaire à coder.
- **Visuels obstacles** : SVG inline simple (cactus = trois rectangles verts, etc.). Pas besoin d'assets.
- **Sprites Boumbi** : 2 frames d'animation alternées en `requestAnimationFrame` (run-left foot, run-right foot). Le SVG Boumbi existant suffit, on peut le scaler/translater.

### Storage
```js
// boumbi-{profile}-runner
{
  bestDistance: 0,       // mètres
  bestLevel: 1,          // niveau max atteint
  unlockedBackgrounds: ['default'],
  totalRuns: 0
}
```

### UI
- Nouvelle entrée sur le home : carte "🦖 Boumbi court" entre Apprendre et Spotify.
- Écran de jeu = canvas plein écran + HUD (vies × 3, distance, niveau actuel).
- Écran de fin = "Tu as fait X m · niveau Y · ⭐⭐ · best : Z m" + bouton Rejouer + bouton Menu.

### Étapes d'implémentation (V1 → V2)
1. **V1** (1 niveau, kick seul) : canvas, Boumbi animé, sol qui défile, cactus qui arrivent, kick = saut/destruction, distance affichée, écran de fin.
2. **V2** : niveaux 2–5, plusieurs pads, sélection de niveau.
3. **V3** : déblocage fonds, leaderboard per-profile.
4. **V4** : intégration Spotify (obstacles en phase avec le BPM cached).

---

## 2. 🦉 Mémo Boumbi (priorité 2)

**Pitch** : Simon-says version drum. Boumbi joue une séquence de pads, à toi de la rejouer. À chaque round réussi, +1 pad dans la séquence.

### Pourquoi
- Format connu et addictif (Simon).
- Travaille la **mémoire courte** + la **précision pad** (associer pad ↔ visuel/son).
- Simple à coder, replay value énorme.
- Pédagogie cachée : aux niveaux élevés, la séquence devient un **vrai pattern** (boum-tac-boum-boum-tac → c'est un pattern reggae).

### Gameplay
1. Boumbi joue une séquence : pour chaque élément, le pad s'allume sur le widget DD-75 + son joue (réutilise les LANE colors).
2. Tour du joueur : il doit taper la même séquence dans le même ordre.
3. Timing **non requis** au début (mémoire pure). Au niveau 5+, ajouter une contrainte de timing facultative.
4. Bonne séquence complète → Boumbi célèbre, +1 pad pour le round suivant.
5. Pad incorrect → game over.

### Modes / difficulté
- **Facile** : 3 pads possibles (snare, kick, hihat). Pour les tout-petits.
- **Medium** : 5 pads.
- **Hard** : tous les pads du DD-75 (10).

### Niveaux
Le round N a N pads dans la séquence. Pas de cap dur. Le record = round atteint.

Tempo de la lecture par Boumbi : ~1.5 pad/seconde au début, accélère légèrement à round 10+ (max 2.5/sec) pour ajouter du challenge mémoire.

### Récompenses
- **Best round atteint** per-profile.
- Stars : 1⭐ à round 3, 2⭐ à round 6, 3⭐ à round 10.
- Petit "wall of fame" : Top 5 best rounds historique par profil.

### Stack technique
- Réutilise les **mini-widgets DD-75** (`lane-widget` / `dd75-layout`) déjà construits pour le mode Apprendre. Un widget centré, gros.
- État : `{sequence: ['snare', 'kick', 'kick', 'hihat'], currentRound: 4, userIndex: 0, mode: 'showing'|'awaiting'|'finished'}`.
- **Phase "showing"** : itère sur `sequence`, pour chaque pad highlight le widget + joue le son (utiliser `freePadHit` avec `isReplay=true`).
- **Phase "awaiting"** : intercepte les hits (MIDI ou clavier), compare au `sequence[userIndex]`.
- Pas de canvas — full DOM/CSS, plus simple.

### Storage
```js
// boumbi-{profile}-memo
{
  bestRound: 0,
  bestRoundByMode: { easy: 0, medium: 0, hard: 0 },
  totalRuns: 0,
  lastRuns: [{ ts, round, mode }]  // pour le wall of fame
}
```

### Hooks de pads pour les tout-petits
Pour le mode "Facile", afficher un grand emoji du pad attendu pendant le tap user (genre 🥁 pour snare). Sert d'indicateur "je dois taper où".

### UI
- Nouvelle carte sur le home : "🦉 Mémo Boumbi".
- Sélecteur de mode (facile/medium/hard) à l'entrée.
- Écran de jeu = grand mini-widget DD-75 au centre, indicateur round/best en haut, "À toi !" ou "Regarde Boumbi" en bas.

### Étapes
1. **V1** (mode medium seul) : séquence, phases show/await, scoring.
2. **V2** : modes facile/hard, wall of fame.
3. **V3** : variant "Mémo Rythme" — la séquence inclut aussi des silences (croches/noires), le timing compte.

---

## 3. 🔁 Echo — Call & Response (priorité 3)

**Pitch** : Boumbi joue une mesure, tu la rejoues. Boumbi en joue une nouvelle, tu suis. Vraie session musicale duo.

### Pourquoi
- C'est exactement comme ça que les vrais batteurs apprennent (prof joue → élève copie).
- Développe **l'oreille rythmique** (entendre puis reproduire).
- Boumbi devient un partenaire, pas juste une mascotte.
- Différent des autres modes : pas de "score arcade", c'est plus posé, presque méditatif.

### Gameplay
1. Boumbi joue une **mesure de 4 temps** (motif généré aléatoirement selon la difficulté).
2. Petit silence (1 mesure) où le joueur entend mentalement ce qu'il vient d'entendre.
3. Joueur rejoue la mesure. Comparer hit-par-hit avec tolérance ±200ms.
4. Si > 70% des hits dans la tolérance → ✅, motif suivant un peu plus dur.
5. Si < 70% → ❌, Boumbi rejoue le même motif (pas de game over, on peut réessayer indéfiniment).
6. Une "session" = 8 motifs. Score final = moyenne des accuracy.

### Difficulté / niveaux
| Niveau | Lanes | Densité | Durée motif |
|---|---|---|---|
| 1 | snare seul | 2 hits/mesure | 1 mesure |
| 2 | snare seul | 4 hits/mesure (♩) | 1 mesure |
| 3 | kick + snare | boum-tac | 1 mesure |
| 4 | kick + snare + hihat | rock basique | 1 mesure |
| 5 | + crash | rock + crash | 1 mesure |
| 6+ | tous | motifs complexes | 2 mesures |

### Génération de motifs
Algorithme simple :
- 16 steps par mesure (double-croches).
- Pour chaque lane active, tirer aléatoirement N positions parmi 16, avec contrainte "pas plus de 2 d'affilée sur la même lane".
- Pour s'assurer que c'est musical : forcer kick sur le temps 1 (step 0) si kick est activé, snare sur le 3 (step 8) si snare actif.

Pas un vrai LLM musical — un simple générateur stochastique avec quelques règles d'aboutissement.

### Récompenses
- **Score par session** sur 100 (moyenne accuracy × 100).
- Stars : 1⭐ à 50%, 2⭐ à 70%, 3⭐ à 90%.
- Best score par niveau, per-profile.

### Stack technique
- Réutilise les fonctions `scheduleNotes` / `playClick` / `drawPlay` du mode Apprendre.
- État : `{currentLevel, motif, phase: 'boumbi-plays'|'silence'|'user-plays'|'eval', userHits[], score}`.
- **Audio Boumbi** : pour chaque hit du motif, programmer un `setTimeout(playClick, t)` ou utiliser `playAccompBeat`.
- **Capture user** : à l'instant t où user-plays démarre, push tous les hits MIDI dans `userHits` avec leur timestamp.
- **Evaluation** : pour chaque hit du motif, chercher dans `userHits` un hit de la même lane dans la fenêtre `[t-200ms, t+200ms]`. % de match.

### Storage
```js
// boumbi-{profile}-echo
{
  bestByLevel: { 1: 95, 2: 88, ... },
  totalSessions: 0,
  totalMotifsDone: 0
}
```

### UI
- Carte "🔁 Echo" sur le home.
- Sélecteur de niveau.
- Écran de jeu :
  - Visuel "Boumbi joue 🎵" / "À toi 🥁" / "Bien joué !" alternés.
  - Grille des 16 steps en bas, animée pendant la phase boumbi.
  - Indicateur de motif courant (4/8), accuracy en live pendant ton tour.

### Étapes
1. **V1** (niveaux 1–3 only) : générateur basique, phases, scoring.
2. **V2** : niveaux 4–6+, visuels améliorés.
3. **V3** : mode "duo libre" — alternance infinie sans niveaux, Boumbi adapte la difficulté à ton accuracy.

---

## 4. 🎨 Studio Boumbi (priorité 4 — le plus gros chantier)

**Pitch** : Step sequencer pour kids. Grille 16 cases × N lanes. Tu cliques pour activer une case. Hit play → ça joue ton motif en loop. Save dans ta bibliothèque, partage avec autre profil.

### Pourquoi
- C'est le "Lego" des drums. Création libre, **pas de bonne/mauvaise réponse**, donc 0 stress.
- Travaille la compréhension de la **structure** d'un beat (1+ 2+ 3+ 4+).
- Précédent qui marche : Groove Pizza, Chrome Music Lab — les kids passent des heures dessus.
- Killer feature : "joue ton motif → Boumbi danse dessus" → l'enfant se sent compositeur.

### Gameplay
- Grille verticale : Y = lanes, X = 16 steps.
- Click sur une cellule → activée (couleur de la lane). Re-click → désactivée.
- Bouton Play → loop infinie de la grille, en sync avec un BPM (slider).
- Stop, Clear, Save.
- Bibliothèque de motifs sauvés (list à gauche). Click sur un motif → chargé dans la grille.
- Bouton "Boumbi danse" → la mascotte fait des animations en sync avec ton motif (kick = bend des genoux, snare = main qui tape, crash = tête qui secoue).

### Lanes par défaut
4 lanes : kick, snare, hihat, crash. (Mode "expert" : toutes les 10 lanes du DD-75.)

### BPM
30 à 200, slider, default 100. Sauvé avec le motif.

### Tempo de la grille
4/4, 16 steps = 1 mesure de double-croches.

Toggle "swing" en bonus (déplace les doubles-croches paires de +30% pour un feeling shuffle).

### Mode jeu = bonus
Une fois ton motif sauvé, le proposer dans le mode **Apprendre** comme un pattern user. Boucle complète : tu composes → tu apprends à le jouer en live.

### Stack technique
- DOM pur (pas de canvas). Une `<div class="step-grid">` avec `data-lane` et `data-step`. Click toggle une classe.
- Audio : Web Audio API existante (`playClick`, `playAccompBeat`). Boucle scheduler à BPM.
- État : `{steps: { kick: [true, false, false, ...], snare: [...] }, bpm, name, createdAt}`.
- Sauvegarde dans `boumbi-{profile}-studio` (array de motifs).

### Storage
```js
// boumbi-{profile}-studio
[
  {
    id: 'mon-premier-beat',
    name: 'Mon premier beat 🎉',
    bpm: 100,
    steps: { kick: [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0], snare: [...], ... },
    createdAt: 1737000000000,
    updatedAt: 1737000000000
  },
  ...
]
```

### UI
- Carte "🎨 Studio Boumbi" sur le home.
- Écran de studio :
  - À gauche : liste des motifs sauvés (cards cliquables, bouton +Nouveau).
  - Au centre : la grille step sequencer.
  - En haut : nom du motif (éditable inline) + boutons Play/Stop/Clear/Save.
  - En bas : Boumbi qui danse pendant le playback.

### Anti-frustration (kids)
- Pas de "score". Vraiment pas. C'est de la création.
- Si grille vide et Play → Boumbi dit "ajoute des notes !" en bulle de speech.
- Couleurs vives par lane (réutilise les LANE.color existants).
- Effets sonores satisfaisants au click (mini "pop").

### Étapes
1. **V1** : grille basique 4 lanes × 16 steps, play/stop/clear, BPM slider, sauvegarde locale.
2. **V2** : bibliothèque (liste + load + delete), nommage des motifs.
3. **V3** : Boumbi qui danse en sync.
4. **V4** : intégration au mode Apprendre (jouer son propre motif en drum hero).
5. **V5** : export → MIDI file téléchargeable.

---

## Ordre d'implémentation recommandé

1. **Boumbi Runner** — killer feature, fun ratio max, replay value.
2. **Mémo Boumbi** — petit en code, gros en addictivité.
3. **Echo** — apport pédagogique fort, mais demande plus de polish UX.
4. **Studio Boumbi** — gros chantier UI, à faire en dernier mais ça transforme l'app en outil créatif.

## Conventions communes à respecter

- **Per-profile** : tout via `pkey('xxx')`. Pas de storage global pour les progrès.
- **Carte home** : ajouter une nouvelle `<button class="card" data-goto="xxx">` dans `#screen-home`, suivre la convention emoji + titre + sous-titre.
- **Back button** : `<button class="btn-back" data-goto="home">←</button>` en haut à gauche.
- **Pill profil** : restera visible en haut à droite — réserver l'espace via `--switcher-w`.
- **MIDI input** : router via `onMIDI` avec un check `currentScreen === 'xxx'`.
- **Calibration** : si un pad est `unmapped`, suggérer le bouton 🎯 (logique existante).
- **Boumbi mascotte** : réutiliser le SVG existant `#boumbi-svg`, le copier dans le nouveau screen avec un id distinct si besoin d'animation séparée.
- **Sons** : réutiliser `freePadHit`, `playClick`, `playAccompBeat`. Pas de samples externes pour l'instant.
