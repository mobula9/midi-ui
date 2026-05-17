# Drum Trainer Kids — PRD

> Application web type "Synthesia pour la batterie" pour enfants de 4 et 6 ans.
> Basée sur le prototype existant `drum-trainer/index.html`, mais repensée pour
> deux pianistes en herbe qui ne savent pas (encore) lire.

---

## 1. Vision

Donner à un enfant de 4 ans **5 minutes d'autonomie joyeuse** sur une batterie
MIDI, sans frustration. À 6 ans, **commencer à comprendre le rythme** via des
patterns visuels simples. Pas d'écran de game-over, pas de "missed", pas de
mode échec : tout est célébration.

Les deux enfants doivent pouvoir s'asseoir devant l'iPad/ordi, ouvrir un
favori, taper sur l'écran avec le doigt **avant** même de jouer sur la
batterie. L'app doit fonctionner toute seule sans qu'un parent intervienne.

---

## 2. Cibles utilisateurs

### 4 ans (cadet)
- Pré-lecteur · vocabulaire visuel : formes, couleurs, animaux, chiffres 1-9
- Coordination motrice fine en cours d'acquisition
- Attention ≈ 2-3 min sur une tâche
- Frustration rapide → besoin de feedback positif constant
- **Veut taper sur quelque chose** et que ça fasse "boum"

### 6 ans (aîné)
- Lit les mots simples (3-4 lettres)
- Coordination motrice acceptable
- Comprend "à tour de rôle", "score", "essaie encore"
- Comprend la notion de tempo
- Commence à reproduire une séquence courte

### Adulte (parent, hors session)
- Configure l'app (MIDI, mapping, profil enfant)
- Consulte les stats/progrès
- Ajoute du contenu (patterns custom, morceaux préférés)

---

## 3. Objectifs

### Critères de succès "joie"
- L'enfant rit ou sourit dans la première minute
- L'enfant **revient** spontanément à l'app le lendemain
- L'enfant termine au moins un pattern complet sans abandonner

### Critères de succès "musical" (6 ans)
- Au bout de 5 sessions, frappe sur le temps (±200ms) sur un pattern simple
- Au bout de 10 sessions, enchaîne kick et snare en alternance sans regarder
- Reconnaît à l'oreille le pattern "rock" vs "disco"

### KPIs simples
- **Temps de session** : 3-10 min (4 ans), 5-15 min (6 ans)
- **Taux de complétion d'un pattern** : > 70% (4 ans) / > 90% (6 ans)
- **Demandes de retour** par jour : ≥ 1

### Anti-KPI
- Score de précision : **non visible par l'enfant**. Pas de note, pas de %.

---

## 4. Hors-scope (V1)

- Lecture de partition / solfège (jamais)
- Notation musicale traditionnelle
- Mode compétition entre joueurs
- Création de patterns par l'enfant
- Partage social / cloud
- Multi-utilisateurs simultanés sur la même app
- Support tablette tactile sans batterie (peut-être plus tard)

---

## 5. Principes UX

### P1 — Tout est visuel, rien à lire
- Icônes/emojis avant les mots
- Sélection par "cartes" avec images, pas de menu déroulant
- Si du texte est nécessaire, gros (≥ 32px), lisible (Atkinson Hyperlegible)

### P2 — Le toucher remplace le clic
- Cibles tactiles ≥ 80×80px
- Pas de double-clic, pas de drag, pas de scroll
- Tout est à 1-2 tap max de profondeur

### P3 — Le feedback est immédiat et positif
- Hit → confettis + son joyeux + mascotte qui sourit
- Manque → pas de signal négatif, juste la note grisée qui descend doucement
- Fin de pattern → animation de fête (ballons, étoiles)

### P4 — L'audio guide
- Une voix off / mascotte annonce les actions ("Allez, on tape ! 🥁")
- Compte à rebours parlé ("4… 3… 2… 1… GO !")
- Encouragements verbaux pendant le jeu

### P5 — Pas d'erreur possible
- Toujours un "Mode libre" accessible (taper sans pattern)
- Le bouton retour ramène à l'écran principal
- Pas de menu paramètres visible (caché derrière long-press 3s)

### P6 — Une session = un cycle court avec récompense
- 30-90 secondes max par pattern
- Récompense visible (animation, étoile dans une collection)
- Bouton "Encore !" ou "Suivant" très grand

---

## 6. Features

### P0 — MVP (à coder en priorité, 1 semaine)

#### Écran d'accueil
- **3 grandes cartes** plein écran : "Mode libre", "Apprendre", "Jouer une chanson"
- Mascotte animée qui salue (un petit personnage qui tape sur un tam-tam)
- Bouton mute audio en coin (petit, pour adulte)

#### Mode libre (tape comme tu veux)
- Pas de notes qui tombent
- Pads en bas, gros, colorés (kick / snare / hi-hat) avec image animale
- Chaque tap déclenche : son drum + animation visuelle (étoile, confetti)
- Score "secret" : nombre de coups, juste pour affichage si tu veux

#### Mode apprendre
- 6 patterns en cartes (icône, nom court "Boum-Tac", BPM)
- Difficulté visualisée par 1 à 5 étoiles
- Compte à rebours visuel + audio "3, 2, 1, GO"
- Notes qui tombent (hérité du proto) mais **plus grosses, plus colorées**
- Hit window très généreux (±300ms à 4 ans, ±200ms à 6 ans)
- Fin de pattern → animation de fête + bouton "Encore" ou "Nouveau"

#### Pads visuels animés (en bas de l'écran)
- **Kick** : icône pied 👟 sur fond rouge — éclat quand frappé
- **Snare** : icône baguettes croisées 🥁 sur fond jaune
- **Hi-Hat** : icône cymbale 🎯 sur fond vert
- Pulse sur frappe + animation de "respiration" au repos

#### Audio
- Click métronome **toujours** (4 ans a besoin de l'aide auditive)
- Voix off optionnelle : "Bravo !", "Trop bien !", "Encore une fois !"
- Sons de récompense (cloches, applaudissements) à la fin

#### Adulte
- Long-press 3s sur le logo en haut → ouvre les réglages (BPM par défaut,
  choix du device MIDI, mapping des notes, calibration des pads, volume voix)

### P1 — V1.0 (semaine 2-3)

- **Profils enfants** : choix entre 2 avatars (Léo / Maya, par exemple)
- **Collection d'étoiles** : chaque pattern terminé donne 1-3 étoiles selon
  régularité ; collection visible sur écran d'accueil (cabinet à trophées)
- **Mascotte qui évolue** : grandit à chaque session (œuf → poussin → poule)
- **Sons mascottes** : remplace les sons drums par animaux (kick = aboiement,
  snare = meow, hi-hat = ding) en mode "rigolo"
- **Mode "jouer une chanson"** : 5-8 morceaux connus (We Will Rock You,
  Hot Cross Buns, Petit Papa Noël, Frère Jacques), drum-track simplifiée

### P2 — Plus tard

- **Mode duo** : deux moitiés d'écran, deux joueurs, deux drums chacun
- **Mode coach IA** : feedback adaptatif sur les patterns ratés
- **Patterns personnalisés** : parent crée un pattern via une interface simple
- **Multi-instruments** : ajout xylo, tambourin, maracas (via UI/écran tactile)
- **Histoire interactive** : Léo le lapin batteur fait une tournée — débloque
  des villes en jouant des patterns

---

## 7. Design visuel

### Palette
- **Fond** : crème doux `#FFF8E7` (pas du blanc clinique, pas du noir froid)
- **Kick** : tomate `#FF6B6B`
- **Snare** : jaune soleil `#FFD93D`
- **Hi-Hat** : vert pomme `#6BCB77`
- **Crash** : violet myrtille `#C77DFF`
- **Mascotte / accents** : turquoise `#4ECDC4`

### Typographie
- **Atkinson Hyperlegible** (Braille Institute, gratuite, hyper lisible)
- Titres : 48-72px
- Boutons : 28-40px
- Pas de gras pour différencier — taille seulement

### Animation
- Toutes les transitions ≥ 200ms (l'enfant doit voir le mouvement)
- Bounce sur tap (scale 1 → 0.85 → 1.05 → 1) — `cubic-bezier(0.34, 1.56, 0.64, 1)`
- Confettis (canvas) à chaque hit, intensité proportionnelle à la précision

### Mascotte
- Personnage animé (SVG ou Lottie) : "Boumbi" le hibou batteur
- États : repos, salut, joue, célèbre, dort (si app inactive)
- Réagit aux hits : applaudit quand on enchaîne 5 coups en série

---

## 8. Audio

### Métronome (toujours actif)
- Click haut sur temps 1 (1500Hz)
- Click bas sur temps 2, 3, 4 (900Hz)
- Volume ajustable (cachée dans réglages adulte)

### Voix off (FR, voix enfantine ou maternelle)
- "Allez, on y va !" au démarrage
- "3, 2, 1, GO !" sur le compte à rebours
- Encouragements aléatoires : "Trop fort !", "Continue !", "Tu déchires !"
- Fin de pattern : "Bravooo !", "Champion !", "Encore une fois ?"

### Sons d'interface
- Tap menu → "blop" doux
- Récompense → cloches montantes
- Erreur → JAMAIS (pas de son négatif)

### Source des sons
- **Boucles drum** : pas nécessaire si DD-75 fait le son (l'enfant entend la
  batterie en physique)
- **SFX UI** : générés via WebAudio (oscillateurs simples) ou samples libres
  (freesound.org sous CC0)
- **Voix** : enregistrement parental personnalisé (faut prévoir un studio
  fichiers wav)

---

## 9. Patterns musicaux

### Niveau 1 — Découverte (4 ans)
| Nom         | Description                                  | BPM | Étoiles |
|-------------|----------------------------------------------|-----|---------|
| Boum boum   | Kick noires                                  | 50  | ★       |
| Tac tac     | Snare noires                                 | 50  | ★       |
| Boum tac    | Kick + Snare alternés (boum-tac-boum-tac)    | 50  | ★★      |

### Niveau 2 — Premier rock
| Nom              | Description                                   | BPM | Étoiles |
|------------------|-----------------------------------------------|-----|---------|
| Rock tout doux   | Boum-tac-boum-tac (croches kick/snare)        | 60  | ★★      |
| We Will Rock You | Pattern Queen avec kick + clap                | 80  | ★★      |
| Boum + tic tic   | Kick + hi-hat constant                        | 60  | ★★★     |

### Niveau 3 — Rock standard (6 ans)
| Nom        | Description                                       | BPM | Étoiles |
|------------|---------------------------------------------------|-----|---------|
| Rock 1     | Pattern rock croches 3 fûts                       | 80  | ★★★     |
| Disco      | Kick partout, snare 2 et 4, hi-hat croches        | 100 | ★★★★    |
| Funky-funk | Funk simplifié                                    | 90  | ★★★★★   |

### Morceaux populaires (P1)
- We Will Rock You (Queen)
- Seven Nation Army (White Stripes) — drum part
- Hot Cross Buns
- Frère Jacques
- Petit Papa Noël
- Happy Birthday (drum simplifié)

---

## 10. Architecture technique

### Stack
- **Frontend** : HTML/CSS/JS pur, pas de framework (page autoportée)
- **Animation** : Canvas 2D + Lottie pour la mascotte
- **MIDI** : Web MIDI API (Chrome / Edge / Brave)
- **Audio** : Web Audio API
- **Local persistence** : `localStorage` pour les profils + collections d'étoiles
- **Pas de backend** dans V1

### Compatibilité
- **OK** : macOS / Windows + Chromium-based browsers
- **OK** : Android Chrome (avec interface USB MIDI OTG)
- **PAS OK V1** : Safari (pas de Web MIDI) → afficher message si Safari détecté
- **PAS OK V1** : iPad (Safari only sur iOS — sauf si on encapsule en
  app native plus tard)

### Pads MIDI
- Mapping par défaut : GM Drum Map (36 kick, 38 snare, 42 hi-hat)
- **Calibration assistée** (P0) : "Tape ton kick maintenant" → enregistre la
  note reçue → écris en localStorage
- Affichage : pad réactif quel que soit le mapping appris

### Performance
- 60 fps stable même sur Chromebook bas de gamme
- Pas de garbage collection visible (réutilisation d'objets dans la game loop)
- Démarrage < 1 sec, latence MIDI → écran < 30 ms

### Structure de code
```
drum-trainer/
├── index.html         # MVP générique (existant)
├── kids.html          # version kids (à coder)
├── PRD-kids.md        # ce document
├── assets/
│   ├── sounds/        # samples wav (cloches, voix off)
│   ├── lottie/        # animations mascotte
│   └── img/           # icônes drums + cartes patterns
├── js/
│   ├── kids-app.js    # logique principale
│   ├── patterns.js    # définition des patterns
│   ├── audio.js       # gestion audio + voix off
│   ├── midi.js        # MIDI input + calibration
│   └── rewards.js     # confettis + animations
└── data/
    ├── voiceover.json # transcription des audios voix
    └── songs.json     # morceaux populaires (P1)
```

---

## 11. Sécurité parentale

- Bouton **paramètres invisible** sans long-press 3 sec
- Mode kiosque (full-screen) après 5 sec d'inactivité dans les menus
- Aucun accès à internet sortant pendant la session (pas de pubs, pas d'API)
- Pas de collecte de données externes (offline-first)
- Backup local des profils → bouton "exporter" dans réglages adulte
- **Time-out de session** optionnel : "C'est l'heure d'arrêter" après 20 min

---

## 12. Tests utilisateur (avec les enfants)

### Avant code
- [ ] Maquette papier des écrans → faire pointer du doigt l'enfant
- [ ] Demander quels animaux ils veulent comme drums (kick=chien ?)

### MVP prêt
- [ ] Session de 5 min avec chacun, sans intervention parentale
- [ ] Observer : où regarde-t-il, où hésite-t-il, où rigole-t-il
- [ ] Aucune indication verbale du parent pendant le test

### Critères go/no-go MVP
- [ ] Le 4 ans trouve "Mode libre" sans aide
- [ ] Le 6 ans termine au moins 1 pattern niveau 1
- [ ] Aucun des deux ne pleure ou ne dit "c'est nul"
- [ ] Au moins une demande de "encore" après la session

---

## 13. Roadmap proposée

| Sprint | Durée  | Livrable                                                    |
|--------|--------|-------------------------------------------------------------|
| S1     | 3 j    | Maquettes statiques + valid avec enfants (papier)           |
| S2     | 5 j    | MVP P0 : 3 écrans (accueil / mode libre / apprendre)       |
| S3     | 2 j    | Calibration MIDI + 3 patterns niveau 1                      |
| S4     | 2 j    | Mascotte Boumbi + voix off basique                          |
| S5     | 3 j    | Patterns niveau 2-3 + animations confettis                  |
| S6     | 3 j    | Tests enfants + ajustements (BPM, taille, sons)             |
| **MVP** | **≈18 j** | **Version utilisable par les enfants**                  |
| S7     | 4 j    | P1 : profils + collection étoiles                           |
| S8     | 5 j    | P1 : morceaux populaires + mascotte évolutive               |
| S9     | 3 j    | P1 : mode rigolo (sons animaux)                             |

---

## 14. Décisions (validées)

1. **Plateforme V1 : ordi uniquement** (Mac/PC + Chrome). Pas d'iPad pour
   l'instant — simplification du scope. L'enfant est devant l'ordi avec le
   DD-75 branché.
2. **Nom : Drum Trainer** (assumé, on garde simple, on changera après les
   tests enfants si besoin).
3. **Mascotte : Boumbi le hibou batteur** 🦉🥁 — SVG inline animé, baguettes
   dans les ailes.
4. **Voix off : pas dans le MVP**. WebAudio tones pour count-in + cloches
   pour récompense. Voix enregistrée parentale en P2.
5. **Sons drums : DD-75 physique** (puisque ordi-only). Pas de synthèse
   logicielle dans le MVP.
6. **Multijoueur : P2** (pas dans le MVP, à voir après usage réel).

---

*Document vivant, à itérer après chaque test enfants.*
