#!/usr/bin/env python3
"""rename_parts_compact.py — compacte le nom des parts au format :

    [Style] Artiste - Chanson (Part N, année, durée).mid

Au lieu de :

    Part NN Label (S-Es) — [Style] Artiste - Chanson (année, durée).mid

Modifie aussi le Title dans le .synthesia. Idempotent : ignore les parts
déjà au nouveau format. Aucune modification du contenu MIDI.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent / "midi" / "annotated"

# Ancien format : "Part NN <label> (S-Es) — <parent_complet>"
OLD_RE = re.compile(r"^Part\s+(?P<num>\d{2,3})\s+.+?\s+\(\d+-\d+s\)\s+—\s+(?P<parent>.+)$")

# Parent complet : "[Style] Artist - Song (year, MmSSs)" + suffix optionnel
# " [Difficulty]" et / ou un disambiguator " (N)" pour les doublons.
PARENT_RE = re.compile(
    r"^(?P<core>.+)\s+"
    r"\((?P<yeardur>[^()]*?(?:\d+m\d+|\?)[^()]*?)\)"
    r"(?P<suffix>(?:\s+\[[^\]]+\])?)"
    r"(?P<dupe>(?:\s+\(\d+\))?)\s*$"
)


def update_title(syn_path: Path, new_title: str) -> bool:
    try:
        tree = ET.parse(syn_path)
    except ET.ParseError:
        return False
    root = tree.getroot()
    song = root.find(".//Song")
    if song is None:
        return False
    if song.get("Title") == new_title:
        return False
    song.set("Title", new_title)
    ET.indent(root, space="  ")
    syn_path.write_bytes(ET.tostring(root, encoding="UTF-8", xml_declaration=True) + b"\n")
    return True


def rename_one(mid_path: Path) -> bool:
    stem = mid_path.stem
    if not stem.startswith("Part "):
        return False  # déjà au nouveau format ou inconnu
    m = OLD_RE.match(stem)
    if not m:
        return False
    pm = PARENT_RE.match(m.group("parent"))
    if not pm:
        return False
    num = int(m.group("num"))
    core = pm.group("core").strip()
    yeardur = pm.group("yeardur").strip()
    suffix = pm.group("suffix").strip()
    dupe = pm.group("dupe").strip()

    new_stem = f"{core} (Part {num}, {yeardur})"
    if suffix:
        new_stem += f" {suffix}"
    if dupe:
        new_stem += f" {dupe}"

    new_mid = mid_path.with_name(new_stem + ".mid")
    if new_mid.exists() and new_mid != mid_path:
        # collision : on suffixe (2), (3) …
        n = 2
        while True:
            cand = mid_path.with_name(f"{new_stem} ({n}).mid")
            if not cand.exists():
                new_mid = cand
                new_stem = new_mid.stem
                break
            n += 1

    if mid_path != new_mid:
        mid_path.rename(new_mid)

    syn = mid_path.with_suffix(".synthesia")
    if syn.exists():
        new_syn = new_mid.with_suffix(".synthesia")
        if syn != new_syn:
            syn.rename(new_syn)
        update_title(new_syn, new_stem)
    return True


def main() -> None:
    n_renamed = 0
    n_skipped = 0
    n_unparsed = 0
    for sub in sorted(ROOT.iterdir()):
        if not sub.is_dir():
            continue
        for mid in sorted(sub.glob("*.mid")):
            stem = mid.stem
            if not stem.startswith("Part "):
                n_skipped += 1
                continue
            if rename_one(mid):
                n_renamed += 1
            else:
                n_unparsed += 1
    print(f"✓ {n_renamed} parts renommés au format compact")
    if n_skipped:
        print(f"  ({n_skipped} déjà au nouveau format)")
    if n_unparsed:
        print(f"  ⚠ {n_unparsed} parts non parsés (format inattendu)")


if __name__ == "__main__":
    main()
