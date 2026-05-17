#!/usr/bin/env python3
"""rename_midis.py — renomme tous les MIDI annotés au format :

    [Style] Artiste - Chanson (année, XmYYs).mid

Et renomme le sous-dossier des parts en conséquence. Les .synthesia
correspondants sont renommés en même temps (l'UniqueId n'est pas affecté).

Métadonnées :
  - Style et année : table interne (par artiste, avec quelques overrides par chanson)
  - Durée : lue depuis le MIDI (mido.MidiFile.length)

Inconnus : préfixés [?] et conservés, à corriger manuellement.
"""
from __future__ import annotations

import re
import shutil
import sys
import unicodedata
from pathlib import Path

import mido

ANNOTATED = Path(__file__).parent / "midi" / "annotated"

# ============================================================================
# Métadonnées
# ============================================================================
# Par artiste : (style, année par défaut si pas d'override par chanson)
ARTIST = {
    # --- Pop moderne ---
    "adele": ("Pop moderne", None),
    "billie eilish": ("Pop moderne", None),
    "billie eilish, khalid": ("Pop moderne", 2020),
    "bruno mars": ("Pop moderne", None),
    "calum scott": ("Pop moderne", 2017),
    "carly rae jepsen": ("Pop moderne", None),
    "celine dion": ("Pop moderne", 1997),
    "cher lloyd": ("Pop moderne", 2012),
    "chord overstreet": ("Pop moderne", 2017),
    "christina perri": ("Pop moderne", None),
    "colbie caillat": ("Pop moderne", 2013),
    "coldplay": ("Pop moderne", None),
    "demi lovato": ("Pop moderne", 2013),
    "duncan laurence": ("Pop moderne", 2019),
    "ed sheeran": ("Pop moderne", None),
    "harry styles": ("Pop moderne", 2017),
    "imagine dragons": ("Pop moderne", None),
    "imagine dragons x j.i.d": ("Pop moderne", 2021),
    "james blunt": ("Pop moderne", 2004),
    "jaymes young": ("Pop moderne", 2017),
    "jessie j": ("Pop moderne", 2013),
    "john legend": ("Pop moderne", 2013),
    "john newman": ("Pop moderne", 2013),
    "jvke": ("Pop moderne", 2022),
    "katy perry": ("Pop moderne", None),
    "kelly clarkson": ("Pop moderne", 2012),
    "labrinth": ("Pop moderne", 2014),
    "lady gaga": ("Pop moderne", None),
    "lana del rey": ("Pop moderne", 2013),
    "lauren daigle": ("Pop moderne", 2018),
    "lewis capaldi": ("Pop moderne", 2018),
    "lily allen": ("Pop moderne", 2013),
    "lorde": ("Pop moderne", 2013),
    "maroon 5": ("Pop moderne", None),
    "miley cyrus": ("Pop moderne", 2013),
    "ne-yo": ("Pop moderne", 2012),
    "olivia rodrigo": ("Pop moderne", 2021),
    "olly murs": ("Pop moderne", 2012),
    "one direction": ("Pop moderne", 2014),
    "onerepublic": ("Pop moderne", 2013),
    "owl city": ("Pop moderne", 2010),
    "passenger": ("Pop moderne", 2012),
    "pink": ("Pop moderne", 2012),
    "rihanna": ("Pop moderne", None),
    "sam smith": ("Pop moderne", 2014),
    "sara bareilles": ("Pop moderne", 2007),
    "selena gomez": ("Pop moderne", 2013),
    "sia": ("Pop moderne", None),
    "stooshe": ("Pop moderne", 2013),
    "syml": ("Pop moderne", 2016),
    "taylor swift": ("Pop moderne", None),
    "the script": ("Pop moderne", 2012),
    "tom odell": ("Pop moderne", 2012),
    "trevor daniel": ("Pop moderne", 2020),
    "5sos": ("Pop moderne", 2014),
    "5 seconds of summer": ("Pop moderne", 2014),
    "the weeknd": ("Pop moderne", None),
    "kina": ("Pop moderne", 2019),

    # --- Pop classique ---
    "the beatles": ("Pop classique", None),
    "beatles": ("Pop classique", None),
    "queen": ("Pop classique", 1975),
    "elton john": ("Pop classique", 1972),
    "billy joel": ("Pop classique", 1973),
    "the police": ("Pop classique", 1983),
    "police": ("Pop classique", 1983),
    "sting": ("Pop classique", 1993),
    "andy williams": ("Pop classique", 1971),
    "bruce hornsby": ("Pop classique", 1986),
    "roxette": ("Pop classique", 1988),
    "bryan adams": ("Pop classique", 1985),
    "elvis presley": ("Pop classique", 1961),
    "george michael": ("Pop classique", 1984),
    "the calling": ("Pop classique", 2001),
    "the fray": ("Pop classique", 2005),
    "the knacks": ("Pop classique", 1979),
    "train": ("Pop classique", 2001),
    "everybody talks": ("Pop classique", 2012),  # Neon Trees
    "capital cities": ("Pop classique", 2011),
    "panic! at the disco": ("Pop classique", 2013),

    # --- Rock / Alternative ---
    "red hot chili peppers": ("Rock", 1991),
    "rhcp": ("Rock", 1991),
    "metallica": ("Rock", 1991),
    "linkin park": ("Rock", None),
    "blink-182": ("Rock", 1999),
    "blink 182": ("Rock", 1999),
    "oasis": ("Rock", 1995),
    "green day": ("Rock", 1997),
    "evanescence": ("Rock", None),
    "system of a down": ("Rock", 2001),
    "bastille": ("Rock", 2013),
    "30 seconds 2 mars": ("Rock", None),
    "30 seconds to mars": ("Rock", None),
    "fall out boy": ("Rock", 2013),
    "foo fighters": ("Rock", None),
    "pixies": ("Rock", 1988),
    "imagine": ("Rock", 1971),  # John Lennon (placeholder if filename = "Imagine")
    "plain white tea's": ("Rock", 2006),
    "second hand serenade": ("Rock", 2008),
    "marshmello": ("Pop moderne", 2018),
    "marshmello ft. bastille": ("Pop moderne", 2018),
    "hozier": ("Pop moderne", 2013),
    "eric clapton": ("Rock", 1992),
    "enya": ("Pop classique", 2000),
    "blackpinck": ("Pop moderne", 2020),  # typo dans filename
    "blackpink": ("Pop moderne", 2020),
    "gary jules": ("Rock", 2001),
    "alec benjamin": ("Pop moderne", 2018),
    "neon trees": ("Pop moderne", 2011),
    "ariana grande": ("Pop moderne", 2014),
    "swedish house mafia": ("Électro", 2012),

    # --- Électro / EDM ---
    "alan walker": ("Électro", None),
    "alan walker & ava max": ("Électro", 2019),
    "alan-walker-k-391": ("Électro", 2018),
    "k-391": ("Électro", 2018),
    "avicii": ("Électro", 2013),
    "calvin harris": ("Électro", 2013),
    "calvin harris ft. ellie goulding": ("Électro", 2013),
    "kygo": ("Électro", 2014),
    "zedd": ("Électro", None),
    "swedish house mafia": ("Électro", 2012),
    "deadmau5": ("Électro", 2010),
    "feed me": ("Électro", 2010),
    "david guetta": ("Électro", 2012),
    "david guetta ft. sia": ("Électro", 2012),
    "massive attack": ("Électro", 1998),
    "despacito": ("Électro", 2017),
    "luis fonsi": ("Électro", 2017),

    # --- Hip-Hop / R&B ---
    "dr dre": ("Hip-Hop", 1999),
    "dr. dre": ("Hip-Hop", 1999),
    "eminem": ("Hip-Hop", 2013),
    "coolio": ("Hip-Hop", 1995),
    "macklemore": ("Hip-Hop", 2012),
    "macklemore & ryan lewis": ("Hip-Hop", 2012),
    "vanilla ice": ("Hip-Hop", 1990),
    "hopsin": ("Hip-Hop", 2014),
    "usher": ("Hip-Hop", 2010),
    "t.i.": ("Hip-Hop", 2014),
    "sir-mix-a-lot": ("Hip-Hop", 1992),
    "ryan leslie": ("Hip-Hop", 2009),
    "guy sebastian": ("Hip-Hop", 2012),
    "cee_lo_green": ("Hip-Hop", 2010),
    "cee lo green": ("Hip-Hop", 2010),

    # --- Classique ---
    "beethoven": ("Classique", None),
    "ludwig van beethoven": ("Classique", None),
    "bach": ("Classique", None),
    "johann sebastian bach": ("Classique", 1722),
    "mozart": ("Classique", 1788),
    "chopin": ("Classique", 1832),
    "liszt": ("Classique", 1850),
    "franz liszt": ("Classique", 1850),
    "brahms": ("Classique", 1853),
    "tchaikovsky": ("Classique", 1876),
    "peter tschaikowsky (die jahreszeiten)": ("Classique", 1876),
    "pachelbel": ("Classique", 1680),
    "johann pachelbel": ("Classique", 1680),
    "rachmaninoff": ("Classique", 1934),
    "sergei rachmaninoff": ("Classique", 1934),
    "shostakovich": ("Classique", 1956),
    "eric thiman": ("Classique", 1953),
    "ennio morricone": ("Classique", None),
    "euphemia_allen": ("Classique", 1877),

    # --- Néo-classique / Piano contemporain ---
    "ludovico einaudi": ("Néo-classique", None),
    "yiruma": ("Néo-classique", 2001),
    "yann tiersen": ("Néo-classique", 2001),
    "yann_tiersen": ("Néo-classique", 2001),
    "imogen heap": ("Néo-classique", 2005),
    "jamie duffy": ("Néo-classique", 2019),
    "keiko_matsui": ("Néo-classique", None),
    "hans zimmer": ("BO Film", None),
    "tuukka jokilehto": ("Néo-classique", None),

    # --- BO Film ---
    "ennio morricone": ("BO Film", None),

    # --- Anime ---
    "unravel_animenz": ("Anime", 2014),
    "sao2": ("Anime", 2014),
    "serhat durmus": ("Électro", 2018),
}

# Overrides chanson (clé = (artist_lower, song_normalized_lower))
SONG_YEAR = {
    ("adele", "hello"): 2015,
    ("adele", "skyfall"): 2012,
    ("billie eilish", "no time to die"): 2020,
    ("billie eilish", "bury a friend"): 2019,
    ("bruno mars", "talking to the moon"): 2010,
    ("bruno mars", "when i was your man"): 2012,
    ("christina perri", "a thousand years"): 2011,
    ("christina perri", "human"): 2014,
    ("christina perri", "jar of hearts"): 2010,
    ("coldplay", "viva la vida"): 2008,
    ("coldplay", "the scientist"): 2002,
    ("coldplay", "clocks"): 2002,
    ("coldplay", "yellow"): 2000,
    ("coldplay", "hymn for the weekend"): 2015,
    ("coldplay", "every teardrop is a waterfall"): 2011,
    ("coldplay", "atlas"): 2013,
    ("coldplay", "a sky full of stars"): 2014,
    ("ed sheeran", "perfect"): 2017,
    ("ed sheeran", "happier"): 2017,
    ("ed sheeran", "autumn leaves"): 2011,
    ("ed sheeran", "you need me i don't need you"): 2011,
    ("ed sheeran", "the a team"): 2011,
    ("ed sheeran", "lego house"): 2011,
    ("imagine dragons", "believer"): 2017,
    ("imagine dragons", "demons"): 2012,
    ("imagine dragons", "radioactive"): 2012,
    ("imagine dragons", "follow you"): 2021,
    ("imagine dragons x j.i.d", "enemy"): 2021,
    ("maroon 5", "payphone"): 2012,
    ("maroon 5", "daylight"): 2012,
    ("maroon 5", "love somebody"): 2012,
    ("maroon 5", "maps"): 2014,
    ("john legend", "all of me"): 2013,
    ("sam smith", "stay with me"): 2014,
    ("lewis capaldi", "someone you loved"): 2018,
    ("taylor swift", "i knew you were trouble"): 2012,
    ("taylor swift", "shake it off"): 2014,
    ("taylor swift", "we are never getting back together"): 2012,
    ("rihanna", "diamonds"): 2012,
    ("rihanna", "stay"): 2013,
    ("sia", "snowman"): 2017,
    ("the weeknd", "save your tears"): 2020,
    ("linkin park", "numb"): 2003,
    ("linkin park", "faint"): 2003,
    ("linkin park", "what i've done"): 2007,
    ("evanescence", "my immortal"): 2003,
    ("evanescence", "lithium"): 2006,
    ("blink-182", "all the small things"): 1999,
    ("blink-182", "adam's song"): 1999,
    ("alan walker", "faded"): 2015,
    ("alan walker", "alone"): 2016,
    ("alan walker", "diamond heart"): 2018,
    ("alan walker", "ignite"): 2018,
    ("zedd", "clarity"): 2012,
    ("zedd", "stay the night"): 2013,
    ("zedd", "break free"): 2014,
    ("dr dre", "still dre"): 1999,
    ("eminem", "rap god"): 2013,
    ("coolio", "gangsta's paradise"): 1995,
    ("macklemore", "thrift shop"): 2012,
    ("macklemore", "white walls"): 2013,
    ("beethoven", "moonlight sonata"): 1801,
    ("beethoven", "sonata no. 17 tempest"): 1802,
    ("beethoven", "fur elise"): 1810,
    ("beethoven", "symphony no 7"): 1812,
    ("ludovico einaudi", "nuvole bianche"): 2004,
    ("ludovico einaudi", "i giorni"): 2001,
    ("ludovico einaudi", "experience"): 2013,
    ("ludovico einaudi", "monday"): 2015,
    ("yiruma", "river flows in you"): 2001,
    ("yann tiersen", "comptine d'un autre ete"): 2001,
    ("hans zimmer", "interstellar"): 2014,
    ("hans zimmer", "first step"): 2014,
    ("hans zimmer", "time"): 2010,
}

# Mapping direct filename → (artist, song, year, style) pour cas spéciaux
# (titres seuls, noms de fichiers exotiques, etc.)
SPECIAL_FILES = {
    "Beautiful Things": ("Benson Boone", "Beautiful Things", 2024, "Pop moderne"),
    "Forever Young": ("Alphaville", "Forever Young", 1984, "Pop classique"),
    "Haddaway": ("Haddaway", "What Is Love", 1993, "Pop classique"),
    "Tom Odell": ("Tom Odell", "Another Love", 2012, "Pop moderne"),
    "Dr Dre": ("Dr. Dre & Snoop Dogg", "Still Dre", 1999, "Hip-Hop"),
    "Gips": ("?", "Gips", None, "?"),
    "Gips 2.aif to MIDI": ("?", "Gips 2", None, "?"),

    "A Thousand Miles": ("Vanessa Carlton", "A Thousand Miles", 2002, "Pop classique"),
    "All of Me": ("John Legend", "All of Me", 2013, "Pop moderne"),
    "Africa_-_Toto": ("Toto", "Africa", 1982, "Pop classique"),
    "Bad Romance Midi": ("Lady Gaga", "Bad Romance", 2009, "Pop moderne"),
    "Children": ("Robert Miles", "Children", 1995, "Électro"),
    "Davy Jones": ("Hans Zimmer", "Davy Jones (Pirates of the Caribbean)", 2006, "BO Film"),
    "Daybreak - Piano Solo in C Major": ("?", "Daybreak", None, "Néo-classique"),
    "Demons (LSAnonymous300)": ("Imagine Dragons", "Demons", 2012, "Pop moderne"),
    "Despacito_Piano_Sheet_Music_Luis_Fonsi_ft_Daddy_Yankee": ("Luis Fonsi & Daddy Yankee", "Despacito", 2017, "Électro"),
    "Die_For_You": ("The Weeknd", "Die For You", 2016, "Pop moderne"),
    "Drink Up Me Hearties": ("Hans Zimmer", "Drink Up Me Hearties (Pirates of the Caribbean)", 2007, "BO Film"),
    "Euphemia_Allen_Chopsticks": ("Euphemia Allen", "Chopsticks", 1877, "Classique"),
    "Everybody Talks": ("Neon Trees", "Everybody Talks", 2012, "Pop moderne"),
    "Experience_-_Ludovico_Einaudi": ("Ludovico Einaudi", "Experience", 2013, "Néo-classique"),
    "Faded": ("Alan Walker", "Faded", 2015, "Électro"),
    "Farewell Hyrule King": ("Koji Kondo", "Farewell Hyrule King (Zelda)", 2006, "Jeux vidéo"),
    "Fall For You - Second Hand Serenade": ("Second Hand Serenade", "Fall For You", 2008, "Rock"),
    "Fur_Elise": ("Beethoven", "Für Elise", 1810, "Classique"),
    "Game_of_Thrones_Easy_piano": ("Ramin Djawadi", "Game of Thrones Main Theme", 2011, "BO Film"),
    "Game_of_Thrones_Main_Theme": ("Ramin Djawadi", "Game of Thrones Main Theme", 2011, "BO Film"),
    "Good_bad_ugly": ("Ennio Morricone", "The Good the Bad and the Ugly", 1966, "BO Film"),
    "Gravity_Falls_Opening_-_Intermediate_Piano_Solo": ("Brad Breeck", "Gravity Falls Opening", 2012, "BO Film"),
    "HTTYD - See You Tomorrow": ("John Powell", "See You Tomorrow (HTTYD)", 2014, "BO Film"),
    "Happy Birthday - Chopin and Liszt style": ("?", "Happy Birthday (Chopin/Liszt style)", None, "Classique"),
    "Hall of Fame - The Script [MIDICollection.net]": ("The Script", "Hall of Fame", 2012, "Pop moderne"),
    "He's a Pirate": ("Hans Zimmer", "He's a Pirate", 2003, "BO Film"),
    "He's a Pirate - Pirates of the Caribbean [MIDICollection.net]": ("Hans Zimmer", "He's a Pirate", 2003, "BO Film"),
    "Hedwig's Theme": ("John Williams", "Hedwig's Theme (Harry Potter)", 2001, "BO Film"),
    "Hotel California": ("Eagles", "Hotel California", 1976, "Pop classique"),
    "Imagine": ("John Lennon", "Imagine", 1971, "Pop classique"),
    "Imogen_Heap_-_Hide_And_Seek": ("Imogen Heap", "Hide and Seek", 2005, "Néo-classique"),
    "Inception - Time": ("Hans Zimmer", "Time (Inception)", 2010, "BO Film"),
    "Interstellar": ("Hans Zimmer", "Interstellar Main Theme", 2014, "BO Film"),
    "Israel IZ Kamakawiwo'ole - Somewhere over the Rainbow - EASY": ("Israel Kamakawiwo'ole", "Somewhere Over the Rainbow", 1993, "Pop classique"),
    "Jessie J - It's My Party": ("Jessie J", "It's My Party", 2013, "Pop moderne"),
    "Jessie J - Thunder": ("Jessie J", "Thunder", 2018, "Pop moderne"),
    "Les Adieux 1st Movement": ("Beethoven", "Les Adieux (1st)", 1810, "Classique"),
    "Les Adieux 2nd Movement": ("Beethoven", "Les Adieux (2nd)", 1810, "Classique"),
    "Liebestraum_No._3_in_A_Major": ("Franz Liszt", "Liebestraum No. 3", 1850, "Classique"),
    "Let Her Go - Passenger [MIDICollection.net]": ("Passenger", "Let Her Go", 2012, "Pop moderne"),
    "Let_Her_Go_Passenger": ("Passenger", "Let Her Go", 2012, "Pop moderne"),
    "Lost Woods": ("Koji Kondo", "Lost Woods (Zelda)", 1998, "Jeux vidéo"),
    "Love_Story_-_Where_Do_I_Begin": ("Andy Williams", "Love Story (Where Do I Begin)", 1971, "Pop classique"),
    "Lovely by Sawser Natho": ("Sawser Natho", "Lovely", None, "?"),
    "Mad World - Gary Jules": ("Gary Jules", "Mad World", 2001, "Rock"),
    "MIDI File - Hans Zimmer - Interstellar (Atlantic Lights Arrangement + Tempo + Key + Colors)": ("Hans Zimmer", "Interstellar Main Theme", 2014, "BO Film"),
    "MIDI File - Keane - Somewhere Only We Know (Atlantic Lights Arrangement + Tempo + Colors + Key)": ("Keane", "Somewhere Only We Know", 2004, "Pop moderne"),
    "Massive Attack - Teardrop": ("Massive Attack", "Teardrop", 1998, "Électro"),
    "My_Life_Is_going_on_-_La_casa_de_papel": ("Cecilia Krull", "My Life Is Going On (Casa de Papel)", 2017, "BO Film"),
    "One Day": ("Asaf Avidan", "One Day (Reckoning Song)", 2008, "Pop moderne"),
    "Paparazzi": ("Lady Gaga", "Paparazzi", 2008, "Pop moderne"),
    "Paradise": ("Coldplay", "Paradise", 2011, "Pop moderne"),
    "Piano Quick Riff - Last Christmas": ("Wham!", "Last Christmas", 1984, "Pop classique"),
    "Piano_Man_Piano": ("Billy Joel", "Piano Man", 1973, "Pop classique"),
    "Piano_See_You_Again_Wiz_Khalifa": ("Wiz Khalifa & Charlie Puth", "See You Again", 2015, "Hip-Hop"),
    "Pixies Where is my mind PIANO - Rinerion": ("Pixies", "Where Is My Mind", 1988, "Rock"),
    "Pompeii": ("Bastille", "Pompeii", 2013, "Rock"),
    "QUEEN - Bohemian Rhapsody": ("Queen", "Bohemian Rhapsody", 1975, "Pop classique"),
    "RHCP - Under The Bridge": ("Red Hot Chili Peppers", "Under the Bridge", 1991, "Rock"),
    "Rain": ("?", "Rain", None, "?"),
    "Requiem_for_a_Dream_Easy": ("Clint Mansell", "Requiem for a Dream", 2000, "BO Film"),
    "River Flows in You - Yiruma [MIDICollection.net]": ("Yiruma", "River Flows in You", 2001, "Néo-classique"),
    "River Flows in You": ("Yiruma", "River Flows in You", 2001, "Néo-classique"),
    "River_Flows_In_You": ("Yiruma", "River Flows in You", 2001, "Néo-classique"),
    "Roar": ("Katy Perry", "Roar", 2013, "Pop moderne"),
    "Rocket Man": ("Elton John", "Rocket Man", 1972, "Pop classique"),
    "See_You_Again_-_Wiz_Khalifa__Charlie_Puth_Piano_Tutorial_": ("Wiz Khalifa & Charlie Puth", "See You Again", 2015, "Hip-Hop"),
    "See_You_Again_Wiz_Khalifa_Charlie_Puth_Piano_Tutorial": ("Wiz Khalifa & Charlie Puth", "See You Again", 2015, "Hip-Hop"),
    "See_You_Again_no_rap": ("Wiz Khalifa & Charlie Puth", "See You Again (no rap)", 2015, "Hip-Hop"),
    "Skyfall": ("Adele", "Skyfall", 2012, "Pop moderne"),
    "Someone you loved": ("Lewis Capaldi", "Someone You Loved", 2018, "Pop moderne"),
    "Sonate_No._14_Moonlight_1st_Movement": ("Beethoven", "Moonlight Sonata (1st)", 1801, "Classique"),
    "Sonate_No._14_Moonlight_3rd_Movement": ("Beethoven", "Moonlight Sonata (3rd)", 1801, "Classique"),
    "Sonatina Opus 36 No. 2 1st Movement": ("Clementi", "Sonatina Op. 36 No. 2 (1st)", 1797, "Classique"),
    "Song of Storms": ("Koji Kondo", "Song of Storms (Zelda)", 1998, "Jeux vidéo"),
    "Stairway_To_Heaven": ("Led Zeppelin", "Stairway to Heaven", 1971, "Rock"),
    "Stairway_to_Heaven_-_Led_Zeppelin": ("Led Zeppelin", "Stairway to Heaven", 1971, "Rock"),
    "Star Wars Main Theme": ("John Williams", "Star Wars Main Theme", 1977, "BO Film"),
    "Still_Dre_-_Dr._Dre_and_Snoop_Dogg": ("Dr. Dre & Snoop Dogg", "Still Dre", 1999, "Hip-Hop"),
    "Still_Dre_Composition": ("Dr. Dre & Snoop Dogg", "Still Dre", 1999, "Hip-Hop"),
    "Summertime_Sadness": ("Lana Del Rey", "Summertime Sadness", 2012, "Pop moderne"),
    "Super Mario Theme-Pianoitall": ("Koji Kondo", "Super Mario Bros. Main Theme", 1985, "Jeux vidéo"),
    "Super_Mario_Bros._-_Main_Theme": ("Koji Kondo", "Super Mario Bros. Main Theme", 1985, "Jeux vidéo"),
    "Tchaikovsky_Piano_Concerto_No1": ("Tchaikovsky", "Piano Concerto No. 1", 1875, "Classique"),
    "The Black Pearl": ("Hans Zimmer", "The Black Pearl (Pirates)", 2003, "BO Film"),
    "The Blood Ritual and Moonlight Serenade": ("?", "The Blood Ritual and Moonlight Serenade", None, "?"),
    "The Final Countdown": ("Europe", "The Final Countdown", 1986, "Rock"),
    "The Imperial March": ("John Williams", "The Imperial March (Star Wars)", 1980, "BO Film"),
    "The Pink Pather Theme": ("Henry Mancini", "The Pink Panther Theme", 1963, "BO Film"),
    "The Police - Every Breath You Take": ("The Police", "Every Breath You Take", 1983, "Pop classique"),
    "The Script feat. will.i.am - Hall of Fame": ("The Script", "Hall of Fame", 2012, "Pop moderne"),
    "The-Daydream-Tears": ("The Daydream", "Tears", 2000, "Néo-classique"),
    "The_Office__Opening_Theme": ("Jay Ferguson", "The Office Theme", 2005, "BO Film"),
    "THIS": ("?", "THIS", None, "?"),
    "Ti_Amo": ("Umberto Tozzi", "Ti Amo", 1977, "Pop classique"),
    "Titanic": ("James Horner", "My Heart Will Go On (Titanic)", 1997, "BO Film"),
    "Titanium": ("David Guetta ft. Sia", "Titanium", 2011, "Électro"),
    "Turret Opera (Cara Mia) - SATB": ("Mike Morasky", "Turret Opera Cara Mia (Portal 2)", 2011, "Jeux vidéo"),
    "Unravel_Animenz_-_Toyko_Ghoul": ("Animenz / TK", "Unravel (Tokyo Ghoul)", 2014, "Anime"),
    "Up is Down": ("Hans Zimmer", "Up is Down (Pirates)", 2007, "BO Film"),
    "Voletarium_Countdown": ("Europa-Park", "Voletarium Countdown", 2017, "BO Film"),
    "Waltz_No._2_by_Shostakovich": ("Shostakovich", "Waltz No. 2", 1956, "Classique"),
    "as_time_goes_by": ("Herman Hupfeld", "As Time Goes By", 1942, "Pop classique"),
    "beliver": ("Imagine Dragons", "Believer", 2017, "Pop moderne"),
    "brahms_opus1_1_format0": ("Brahms", "Piano Sonata Op. 1 (1st)", 1853, "Classique"),
    "brahms_opus1_2_format0": ("Brahms", "Piano Sonata Op. 1 (2nd)", 1853, "Classique"),
    "brahms_opus1_3_format0": ("Brahms", "Piano Sonata Op. 1 (3rd)", 1853, "Classique"),
    "brahms_opus1_4_format0": ("Brahms", "Piano Sonata Op. 1 (4th)", 1853, "Classique"),
    "break_free_-_ariana_grande_feat._zedd_arr._by_fonzi_m": ("Ariana Grande ft. Zedd", "Break Free", 2014, "Électro"),
    "bruce_hornsby-the_way_it_is": ("Bruce Hornsby", "The Way It Is", 1986, "Pop classique"),
    "cee_lo_green-forget_you": ("Cee Lo Green", "Forget You", 2010, "Hip-Hop"),
    "coldplay-a_sky_full_of_stars": ("Coldplay", "A Sky Full of Stars", 2014, "Pop moderne"),
    "deadmau5_-_Strobe_(Evan_Duffy_Piano_Version)": ("deadmau5", "Strobe", 2010, "Électro"),
    "deep end": ("?", "Deep End", None, "?"),
    "elise_format0": ("Beethoven", "Für Elise", 1810, "Classique"),
    "keiko_matsui_midnight_stone": ("Keiko Matsui", "Midnight Stone", None, "Néo-classique"),
    "les_choristes_cerf_volant": ("Bruno Coulais", "Cerf-Volant (Les Choristes)", 2004, "BO Film"),
    "les_choristes_vois_sur_ton_chemin1": ("Bruno Coulais", "Vois sur ton chemin (Les Choristes)", 2004, "BO Film"),
    "mak - idk": ("?", "idk", None, "?"),
    "night_2_is_ee_the_stars": ("?", "Night 2 (See the Stars)", None, "?"),
    "nocturne_9_2": ("Chopin", "Nocturne Op. 9 No. 2", 1832, "Classique"),
    "passenger-let_her_go": ("Passenger", "Let Her Go", 2012, "Pop moderne"),
    "radioactiv": ("Imagine Dragons", "Radioactive", 2012, "Pop moderne"),
    "roxette-listen_to_your_heart": ("Roxette", "Listen to Your Heart", 1988, "Pop classique"),
    "sao2_-_ed_startear_piano_by_fonzi_m_remastered_for_upload": ("LiSA / SAO", "Startear (SAO II ED)", 2014, "Anime"),
    "sara_bareilles-love_song": ("Sara Bareilles", "Love Song", 2007, "Pop moderne"),
    "ses_Death": ("?", "Death (SES)", None, "?"),
    "stay_the_night_-_zedd_ft._hayley_williams_fonzimgm": ("Zedd ft. Hayley Williams", "Stay the Night", 2013, "Électro"),
    "train-drops_of_jupiter": ("Train", "Drops of Jupiter", 2001, "Pop classique"),
    "wounderful_world": ("Louis Armstrong", "What a Wonderful World", 1967, "Pop classique"),
    "yann_tiersen-comptine_dun_autre_ete": ("Yann Tiersen", "Comptine d'un autre été", 2001, "Néo-classique"),
    "Olly Murs - Right Place Right Time (Pianoitall.com)": ("Olly Murs", "Right Place Right Time", 2012, "Pop moderne"),
    "Owl City - Fireflies  PIANO - Rinerion": ("Owl City", "Fireflies", 2009, "Pop moderne"),
    "Owl City feat. Carly Rae Jepsen - Good Time": ("Owl City & Carly Rae Jepsen", "Good Time", 2012, "Pop moderne"),
    "Panic! At The Disco- GirlsGirlsBoys": ("Panic! At The Disco", "Girls/Girls/Boys", 2013, "Rock"),
    "Sting - Shape Of My Heart": ("Sting", "Shape of My Heart", 1993, "Pop classique"),
    "Lady Gaga - Applause": ("Lady Gaga", "Applause", 2013, "Pop moderne"),
    "Sergei Rachmaninoff - Rhapsody on a Theme of Paganini - Variation 18": ("Rachmaninoff", "Rhapsody on a Theme of Paganini Var. 18", 1934, "Classique"),
    "Serhat Durmus - La Cネin": ("Serhat Durmus", "La Câlin", 2018, "Électro"),
    "S派ne Mannheims - Und Wenn Ein Lied": ("Söhne Mannheims", "Und Wenn Ein Lied", 2004, "Pop classique"),
    "Mad world (hands are divided)": ("Gary Jules", "Mad World", 2001, "Rock"),
    "Where is my mind (hands are divided)": ("Pixies", "Where Is My Mind", 1988, "Rock"),
    "Adam's Song - Blink 182 - Rinerion": ("Blink-182", "Adam's Song", 1999, "Rock"),
    "50 Ways to Say Goodbye": ("Train", "50 Ways to Say Goodbye", 2012, "Pop classique"),
    "5 Beautiful songs (hands are divided)": ("?", "5 Beautiful songs (medley)", None, "?"),
    "Alan Walker Faded": ("Alan Walker", "Faded", 2015, "Électro"),
    "Alan_Walker_Faded": ("Alan Walker", "Faded", 2015, "Électro"),
    "Alan-Walker-K-391-IGNITE-MIDI": ("Alan Walker & K-391", "Ignite", 2018, "Électro"),
    "Alone - Alan Walker (hands are divided)": ("Alan Walker", "Alone", 2016, "Électro"),
    "BLACKPINCK - How You Like That (hands are divided)": ("BLACKPINK", "How You Like That", 2020, "Pop moderne"),
    "Beethoven_Symphony_No7": ("Beethoven", "Symphony No. 7", 1812, "Classique"),
    "Beethoven Symphony No7": ("Beethoven", "Symphony No. 7", 1812, "Classique"),
    "Call Me Maybe - Carly Rae Jepsen [MIDICollection.net]": ("Carly Rae Jepsen", "Call Me Maybe", 2011, "Pop moderne"),
    "Coldplay - Clocks (Adrian Lee Piano Version)": ("Coldplay", "Clocks", 2002, "Pop moderne"),
    "Coldplay_-_Clocks_(Adrian_Lee_Piano_Version)": ("Coldplay", "Clocks", 2002, "Pop moderne"),
    "Coldplay_-_Yellow_(Adrian_Lee_Piano_Version)": ("Coldplay", "Yellow", 2000, "Pop moderne"),
    "Death (SES)": ("?", "Death (SES)", None, "?"),
    "Deep End (hands are divided)": ("?", "Deep End", None, "?"),
    "Ed_Sheeran_Perfect_Piano_Cover": ("Ed Sheeran", "Perfect", 2017, "Pop moderne"),
    "Enya - Only Time": ("Enya", "Only Time", 2000, "Pop classique"),
    "Eric Clapton - Tears In Heaven (Advanced)": ("Eric Clapton", "Tears in Heaven", 1992, "Rock"),
    "Feed_Me_+_Ellie_Goulding_-_Relocating_The_Lights_(Evan_Duffy_Piano_Version)": ("Feed Me & Ellie Goulding", "Relocating the Lights", 2010, "Électro"),
    "Gary Jules - Mad World": ("Gary Jules", "Mad World", 2001, "Rock"),
    "Hozier - take me to church (hands are divided)": ("Hozier", "Take Me to Church", 2013, "Pop moderne"),
    "Metallica - Nothing Else Matters piano solo": ("Metallica", "Nothing Else Matters", 1991, "Rock"),
    "Metallica_-_Nothing_Else_Matters_piano_solo": ("Metallica", "Nothing Else Matters", 1991, "Rock"),
    "Monday - Ludovico Einaudi": ("Ludovico Einaudi", "Monday", 2015, "Néo-classique"),
    "Monday - Ludovico Einaudi (2)mid": ("Ludovico Einaudi", "Monday", 2015, "Néo-classique"),
    "Night 2 (See the Stars)": ("?", "Night 2", None, "?"),
    "Rain": ("?", "Rain", None, "?"),
    "Sawser Natho - Lovely": ("Billie Eilish & Khalid", "Lovely", 2018, "Pop moderne"),
    "Yann_Tiersen_-_Comptine_Dun_Autre_Ete__Lapres_Midi": ("Yann Tiersen", "Comptine d'un autre été (l'après-midi)", 2001, "Néo-classique"),
    "blink-182_All_the_small_things_MIDI": ("Blink-182", "All the Small Things", 1999, "Rock"),
    "Imagine Dragons x J.I.D - Enemy (hands are divide)": ("Imagine Dragons & JID", "Enemy", 2021, "Pop moderne"),
    "Imagine Dragons x J.I.D - Enemy (hands are divided)": ("Imagine Dragons & JID", "Enemy", 2021, "Pop moderne"),
    "Imagine.mid": ("John Lennon", "Imagine", 1971, "Pop classique"),
    "Imagine": ("John Lennon", "Imagine", 1971, "Pop classique"),
    "5sos - Heartbreak Girl - Pianoitall": ("5 Seconds of Summer", "Heartbreak Girl", 2014, "Pop moderne"),
    "Andy Williams - Love Story Where Do I Begin": ("Andy Williams", "Love Story (Where Do I Begin)", 1971, "Pop classique"),
    "Colbie Caillat - Try - Pianoitall": ("Colbie Caillat", "Try", 2014, "Pop moderne"),
    "Coolio - Gangsta's Paradise [Remake] (hands are divided)": ("Coolio", "Gangsta's Paradise [Remake]", 1995, "Hip-Hop"),
    "John Legend - All of Me - Pianoitall": ("John Legend", "All of Me", 2013, "Pop moderne"),
    "Macklemore - White Walls": ("Macklemore", "White Walls", 2013, "Hip-Hop"),
    "Maroon 5 - Daylight (Pianoitall.com)": ("Maroon 5", "Daylight", 2012, "Pop moderne"),
    "Maroon 5 - Maps - Pianoitall": ("Maroon 5", "Maps", 2014, "Pop moderne"),
    "Sam Smith - Stay With Me - Pianoitall": ("Sam Smith", "Stay With Me", 2014, "Pop moderne"),
    "Taylor Swift - Shake It Off - Pianoitall": ("Taylor Swift", "Shake It Off", 2014, "Pop moderne"),
    "Taylor Swift - we are never getting back together": ("Taylor Swift", "We Are Never Getting Back Together", 2012, "Pop moderne"),
    "One Direction - Steal My Girl - Pianoitall": ("One Direction", "Steal My Girl", 2014, "Pop moderne"),
    "Demons (LSAnonymous300)": ("Imagine Dragons", "Demons", 2012, "Pop moderne"),
    "Faded.mid": ("Alan Walker", "Faded", 2015, "Électro"),
    "Tom Odell - Another love (hands are divided)": ("Tom Odell", "Another Love", 2012, "Pop moderne"),
    "Alan Walker - Faded [Rousseau Cover MIDI]": ("Alan Walker", "Faded", 2015, "Électro"),
    "Alan Walker - Faded": ("Alan Walker", "Faded", 2015, "Électro"),
    "Billie Eilish - bury a friend [Rousseau Cover MIDI]": ("Billie Eilish", "bury a friend", 2019, "Pop moderne"),
    "John Legend - All of Me [Rousseau Cover MIDI]": ("John Legend", "All of Me", 2013, "Pop moderne"),
    "Adele - Skyfall (Pianoitall.com)": ("Adele", "Skyfall", 2012, "Pop moderne"),
    "Adele - hello (hands are divided)": ("Adele", "Hello", 2015, "Pop moderne"),
    "Alan Walker & Ava Max - Alone, Pt. II (Hands are divided)": ("Alan Walker & Ava Max", "Alone Pt. II", 2019, "Électro"),
    "Demi Lovato - Heart Attack (Pianoitall.com)": ("Demi Lovato", "Heart Attack", 2013, "Pop moderne"),
    "Beethoven - Moonlight Sonata (Pianoitall.com)": ("Beethoven", "Moonlight Sonata", 1801, "Classique"),
    "Bruno Mars - When I Was Your Man (Pianoitall.com)": ("Bruno Mars", "When I Was Your Man", 2012, "Pop moderne"),
    "Ed Sheeran - The A Team(Pianoitall.com)": ("Ed Sheeran", "The A Team", 2011, "Pop moderne"),
    "Sia - Snowman (hands are divided)": ("Sia", "Snowman", 2017, "Pop moderne"),
    "Linkin park - Numb": ("Linkin Park", "Numb", 2003, "Rock"),
    "Linkin Park - Faint (hands are divided)": ("Linkin Park", "Faint", 2003, "Rock"),
    "Linkin Park - What I've Done (hands are divided)": ("Linkin Park", "What I've Done", 2007, "Rock"),
    "Ludovico Einaudi - Experience (hands are divided)": ("Ludovico Einaudi", "Experience", 2013, "Néo-classique"),
    "Bruno Mars - Talking to the moon (hands are divided)": ("Bruno Mars", "Talking to the Moon", 2010, "Pop moderne"),
    "Billie Eilish - No Time To Die (hands are divided)": ("Billie Eilish", "No Time to Die", 2020, "Pop moderne"),
    "Coldplay - Hymn For The Weekend (hands are divided)": ("Coldplay", "Hymn for the Weekend", 2015, "Pop moderne"),
    "Coolio - Gangsta's Paradise (hands are divided)": ("Coolio", "Gangsta's Paradise", 1995, "Hip-Hop"),
    "Duncan Laurence feat. Fletcher - Arcade (hands are divided)": ("Duncan Laurence", "Arcade", 2019, "Pop moderne"),
    "Imagine Dragons - Follow you (hands are divided)": ("Imagine Dragons", "Follow You", 2021, "Pop moderne"),
    "Jaymes Young - Infinity (hands are divided)": ("Jaymes Young", "Infinity", 2014, "Pop moderne"),
    "Kina - Get you the moon (hands are divided)": ("Kina", "Get You the Moon", 2019, "Pop moderne"),
    "Passenger - Let Her Go (hands are divided)": ("Passenger", "Let Her Go", 2012, "Pop moderne"),
    "System Of A Down - Chop Suey! (hands are divided)": ("System of a Down", "Chop Suey!", 2001, "Rock"),
    "The Weeknd - Save Your Tears (hands are divided)": ("The Weeknd", "Save Your Tears", 2020, "Pop moderne"),
    "Trevor Daniel - Falling (hands are divided)": ("Trevor Daniel", "Falling", 2020, "Pop moderne"),
    "Time - Zimmer (hands are divided)": ("Hans Zimmer", "Time (Inception)", 2010, "BO Film"),
    "Marshmello ft. Bastille - Happier": ("Marshmello & Bastille", "Happier", 2018, "Pop moderne"),
    "Lana Del Rey - Young and Beautiful": ("Lana Del Rey", "Young and Beautiful", 2013, "Pop moderne"),
    "Ed_Sheeran_Perfect_Piano_Cover.mid": ("Ed Sheeran", "Perfect", 2017, "Pop moderne"),
    "Let me down slowly (hands are divided)": ("Alec Benjamin", "Let Me Down Slowly", 2018, "Pop moderne"),
    "Time - Zimmer (hands are divided)": ("Hans Zimmer", "Time (Inception)", 2010, "BO Film"),
    "deep end (hands are divided)": ("?", "Deep End", None, "?"),
    "mak - idk (hands are divided)": ("?", "idk", None, "?"),
    "Zelda's Lullaby": ("Koji Kondo", "Zelda's Lullaby", 1998, "Jeux vidéo"),
}

ZELDA_OOT_TRACKS = [
    "Bolero Of Fire", "Fairy Flying", "Fairy Fountain", "Ganondorfs Theme",
    "Gerudo Valley", "Goron City", "Great Deku Trees Last Words",
    "Hyrule Castle Courtyard", "Hyrule Field", "Ice Cavern", "Inside A House",
    "Inside The Deku Tree", "Kaepora Gaebora", "Kakariko Village", "Kokiri Forest",
    "Kotake And Koume", "Lon Lon Ranch", "Lost Woods", "Market", "Master Sword",
    "Minuet Of Forest", "Nocturne Of Shadow", "Opening Title", "Potion Shop",
    "Prelude Of Light", "Requiem Of Spirit", "Serenade Of Water", "Sheiks Theme",
    "Shop", "Spirit Temple", "Spiritual Stone", "Temple Of Time", "Treasure Chest",
    "Windmill Hut", "Zeldas Lullaby", "Zoras Domain",
]


def normalize(s: str) -> str:
    """Lowercase + strip + remove diacritics for keys."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def parse_filename(stem: str) -> tuple[str | None, str]:
    """Tente d'extraire (artist, song) depuis un nom de fichier libre."""
    cleaned = stem
    for marker in [
        " (hands are divided)", " (hands are divide)", " (Hands are divided)",
        " (HARD)", " (Hard)", " (Hard Version)", " (Harder)",
        " (Advanced)", " (Simple)", " (Beginner)", " (Easy)", " (EASY)",
        " (Pianoitall.com)", " - Pianoitall", " [MIDICollection.net]",
        " [Rousseau Cover MIDI]", " - Rinerion", " - PIANO - Rinerion",
        " PIANO - Rinerion", " feat. will.i.am",
        " (1)", " (2)",
        " (Atlantic Lights Arrangement + Tempo + Colors + Key)",
        " (Atlantic Lights Arrangement + Tempo + Key + Colors)",
        " (Atlantic Lights Arrangement + Tempo +Key +Colors)",
        " (Atlantic Lights Arrangement + Tempo + Key +Colors)",
        "Full MIDI - ", "Full MIDI- ", "MIDI File - ",
    ]:
        cleaned = cleaned.replace(marker, "")
    cleaned = cleaned.strip()

    # Underscores → spaces (TOUJOURS, pas seulement si absence de " - ")
    cleaned = re.sub(r"_+", " ", cleaned).strip()

    if " - " not in cleaned:
        return None, cleaned

    parts = cleaned.split(" - ", 1)
    artist = parts[0].strip()
    song = parts[1].strip() if len(parts) > 1 else ""
    return artist or None, song or cleaned


DIFFICULTY_MARKERS = [
    ("Advanced", ["(Advanced)"]),
    ("Hard", ["(Hard Version)", "(Hard)", "(Harder)", "(HARD)"]),
    ("Simple", ["(Simple)"]),
    ("Beginner", ["(Beginner)"]),
    ("Easy", ["(Easy)", "(EASY)", "- EASY"]),
]

INFO_MARKERS = [
    ("Rousseau cover", ["[Rousseau Cover MIDI]", "Rousseau Cover", "Rousseau"]),
    ("Pianoitall.com", ["(Pianoitall.com)", "- Pianoitall", "Pianoitall"]),
    ("MIDICollection.net", ["[MIDICollection.net]", "MIDICollection"]),
    ("Rinerion", ["- Rinerion", "PIANO - Rinerion", "Rinerion"]),
    ("Atlantic Lights Arrangement", ["Atlantic Lights"]),
    ("hands divided", ["hands are divided", "hands are divide", "Hands are divided"]),
    ("Adrian Lee Piano Version", ["Adrian Lee"]),
    ("Fonzi M arrangement", ["fonzi"]),
    ("Evan Duffy Piano Version", ["Evan Duffy"]),
]


def get_metadata(stem: str) -> tuple[str, str, int | None, str, str, str]:
    """Retourne (artist, song, year, style, difficulty_tag, info_subtitle).

    - difficulty_tag : "Advanced"/"Easy"/etc. (apparaît dans le filename)
    - info_subtitle  : "hands divided; Rousseau cover" (migre dans .synthesia Subtitle)
    """
    s_low = stem.lower()
    difficulty = ""
    for tag, markers in DIFFICULTY_MARKERS:
        if any(m.lower() in s_low for m in markers):
            difficulty = tag
            break

    info_tags: list[str] = []
    for label, markers in INFO_MARKERS:
        if any(m.lower() in s_low for m in markers):
            info_tags.append(label)
    info_subtitle = "; ".join(info_tags)

    # 0. Tracks Zelda OoT
    for track in ZELDA_OOT_TRACKS:
        if stem.startswith(f"Zelda Ocarina of Time - {track}"):
            return ("Koji Kondo", f"{track} (Zelda)", 1998, "Jeux vidéo", difficulty, info_subtitle)

    # 1. Override par filename complet (cherche par lookup direct ou par préfixe)
    if stem in SPECIAL_FILES:
        a, s, y, st = SPECIAL_FILES[stem]
        return (a, s, y, st, difficulty, info_subtitle)
    for key, (a, s, y, st) in SPECIAL_FILES.items():
        if stem.startswith(key):
            return (a, s, y, st, difficulty, info_subtitle)

    # 2. Parse artist/song depuis le nom
    artist, song = parse_filename(stem)
    if artist is None:
        return ("?", song or stem, None, "?", difficulty, info_subtitle)

    # 3. Look up dans la table ARTIST
    artist_norm = normalize(artist)
    if artist_norm not in ARTIST:
        artist_norm_short = re.split(r"\s+(?:ft\.|feat\.|featuring|&)\s+", artist_norm)[0].strip()
        if artist_norm_short in ARTIST:
            artist_norm = artist_norm_short
        else:
            return (artist, song, None, "?", difficulty, info_subtitle)

    style, default_year = ARTIST[artist_norm]
    song_norm = normalize(re.sub(r"\s*\(.*?\)\s*", "", song))
    year = SONG_YEAR.get((artist_norm, song_norm), default_year)
    return (artist, song, year, style, difficulty, info_subtitle)


def fmt_duration(sec: float) -> str:
    """Formate des secondes en 'XmYYs'. Cap à 99 min en cas d'aberration."""
    if sec > 99 * 60 or sec < 0:
        return "?"
    m, s = divmod(int(round(sec)), 60)
    return f"{m}m{s:02d}"


def safe_filename(name: str) -> str:
    # Sur macOS, seul '/' est interdit. On garde '?' pour signaler les inconnus.
    return name.replace("/", "_").strip()


def build_new_name(stem: str, duration_s: float) -> tuple[str, str]:
    """Retourne (nouveau_nom_sans_extension, info_subtitle_pour_synthesia)."""
    artist, song, year, style, difficulty, info_subtitle = get_metadata(stem)
    dur = fmt_duration(duration_s)
    style_tag = f"[{style}]"
    year_part = f"{year}, {dur}" if year else (f"?, {dur}" if dur != "?" else "?")
    diff_part = f" [{difficulty}]" if difficulty else ""
    if artist == "?" or not artist:
        new_name = f"{style_tag} {song} ({year_part}){diff_part}"
    else:
        new_name = f"{style_tag} {artist} - {song} ({year_part}){diff_part}"
    return safe_filename(new_name), info_subtitle


def main() -> None:
    if not ANNOTATED.exists():
        print(f"⚠️  {ANNOTATED} n'existe pas")
        sys.exit(1)

    # Étape 1 : renomme les .mid + .synthesia à la racine
    mid_files = sorted(ANNOTATED.glob("*.mid"))
    print(f"→ {len(mid_files)} fichiers complets à renommer")

    used_names: dict[str, int] = {}
    renames: list[tuple[Path, Path, Path | None, Path | None]] = []
    # (mid_src, mid_dst, syn_src, syn_dst)  – pour les paires complètes
    dir_renames: list[tuple[Path, Path]] = []  # (src_dir, dst_dir)
    # syn_dst → info_subtitle à écrire dans le .synthesia après renommage
    subtitle_for: dict[Path, str] = {}

    for mid in mid_files:
        # Idempotence : skip si déjà au format [...] X
        if mid.stem.startswith("["):
            continue
        try:
            duration_s = mido.MidiFile(mid).length
        except Exception:
            duration_s = -1
        base_new, info_subtitle = build_new_name(mid.stem, duration_s)

        # Déduplique si collision
        candidate = base_new
        n = used_names.get(candidate.lower(), 0)
        if n > 0:
            candidate = f"{base_new} ({n+1})"
        used_names[base_new.lower()] = n + 1

        mid_dst = mid.with_name(candidate + ".mid")
        syn_src = mid.with_suffix(".synthesia")
        syn_dst = mid_dst.with_suffix(".synthesia") if syn_src.exists() else None

        renames.append((mid, mid_dst, syn_src if syn_src.exists() else None, syn_dst))
        if info_subtitle and syn_dst is not None:
            subtitle_for[syn_dst] = info_subtitle

        # Sous-dossier des parts ?
        parts_dir = mid.with_suffix("")
        if parts_dir.is_dir():
            dir_renames.append((parts_dir, parts_dir.with_name(candidate)))

    # Applique (deux passes pour éviter les collisions intermédiaires)
    # Pass 1 : renomme via noms temporaires uniques
    tmp_renames = []
    for i, (src, dst, syn_src, syn_dst) in enumerate(renames):
        if src == dst:
            continue
        tmp = src.with_name(f"__tmp_{i}__{src.name}")
        src.rename(tmp)
        tmp_syn = None
        if syn_src is not None:
            tmp_syn = syn_src.with_name(f"__tmp_{i}__{syn_src.name}")
            syn_src.rename(tmp_syn)
        tmp_renames.append((tmp, dst, tmp_syn, syn_dst))

    for i, (src_dir, dst_dir) in enumerate(dir_renames):
        if src_dir == dst_dir:
            continue
        tmp = src_dir.with_name(f"__tmp_{i}__{src_dir.name}")
        src_dir.rename(tmp)
        dir_renames[i] = (tmp, dst_dir)

    # Pass 2 : renomme du temp vers le nom final
    n_done = 0
    for src, dst, syn_src, syn_dst in tmp_renames:
        src.rename(dst)
        if syn_src is not None and syn_dst is not None:
            syn_src.rename(syn_dst)
        n_done += 1

    n_dirs = 0
    for src_dir, dst_dir in dir_renames:
        if src_dir.exists():
            src_dir.rename(dst_dir)
            n_dirs += 1

    # Étape 3 : renomme aussi les parts à l'intérieur de chaque sous-dossier
    # Format cible (matche le Title) :
    #   Part NN <label> (S-Es) — <nom du dossier parent>.mid
    n_parts = 0
    part_re = re.compile(r"^(?P<num>\d{2,3})\s*-\s*(?P<rest>.+)$")
    for sub in sorted(ANNOTATED.iterdir()):
        if not sub.is_dir():
            continue
        parent_stem = sub.name
        for mid in sorted(sub.glob("*.mid")):
            stem = mid.stem
            if stem.startswith("Part "):
                continue  # idempotent
            m = part_re.match(stem)
            if not m:
                continue
            new_stem = f"Part {m['num']} {m['rest']} — {parent_stem}"
            new_stem = safe_filename(new_stem)
            new_mid = mid.with_name(new_stem + ".mid")
            mid.rename(new_mid)
            syn = mid.with_suffix(".synthesia")
            if syn.exists():
                syn.rename(new_mid.with_suffix(".synthesia"))
            n_parts += 1

    # Étape 4 : écrit l'attribut Subtitle dans les .synthesia (full + parts)
    import xml.etree.ElementTree as ET
    n_sub = 0
    for syn_path, subtitle in subtitle_for.items():
        if not syn_path.exists():
            continue
        try:
            tree = ET.parse(syn_path)
            root = tree.getroot()
            song = root.find(".//Song")
            if song is not None:
                song.set("Subtitle", subtitle)
                ET.indent(root, space="  ")
                syn_path.write_bytes(ET.tostring(root, encoding="UTF-8", xml_declaration=True) + b"\n")
                n_sub += 1
        except ET.ParseError:
            pass
        # Propage le Subtitle aux parts du sous-dossier correspondant
        parts_dir = syn_path.with_suffix("")
        if parts_dir.is_dir():
            for part_syn in parts_dir.glob("*.synthesia"):
                try:
                    tree = ET.parse(part_syn)
                    root = tree.getroot()
                    song = root.find(".//Song")
                    if song is not None:
                        song.set("Subtitle", subtitle)
                        ET.indent(root, space="  ")
                        part_syn.write_bytes(ET.tostring(root, encoding="UTF-8", xml_declaration=True) + b"\n")
                        n_sub += 1
                except ET.ParseError:
                    pass

    # Compte les fichiers unknowns
    unknown = sum(1 for _, dst, _, _ in renames if "[?]" in dst.name)

    print(f"✓ {n_done} fichiers complets renommés (.mid + .synthesia)")
    print(f"✓ {n_dirs} sous-dossiers de parts renommés")
    print(f"✓ {n_parts} fichiers de parts renommés au format complet")
    print(f"✓ {n_sub} Subtitle écrits dans les .synthesia (source/arrangement)")
    print(f"⚠ {unknown} fichiers sans métadonnées identifiées (préfixe [?])")


if __name__ == "__main__":
    main()
