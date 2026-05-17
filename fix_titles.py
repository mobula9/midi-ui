#!/usr/bin/env python3
"""fix_titles.py — réécrit l'attribut Title dans tous les .synthesia
pour qu'il corresponde au nom de fichier (sans extension).

Synthesia affiche ce Title, pas le filename. Sans ça, on garde l'ancien
nom moche après renommage.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).parent / "midi" / "annotated"

# Filename de part : depuis rename_midis, le nom inclut déjà toute l'info
# ("Part NN <label> (S-Es) — [Style] Artiste - Chanson (année, durée)").
# Sinon (legacy "NN - <label>"), on assemble avec le nom du parent.
PART_NAME_RE = re.compile(r"^(\d{2,3})\s*-\s*(.+)$")


def title_from_filename(stem: str, is_part: bool, parent_stem: str | None) -> str:
    """Title = stem du fichier (ils sont maintenant synchronisés).

    Fallback legacy : si on tombe sur un ancien nom 'NN - label', on assemble
    quand même avec le parent.
    """
    if stem.startswith("Part ") or not is_part or not parent_stem:
        return stem
    m = PART_NAME_RE.match(stem)
    if m:
        num, label = m.group(1), m.group(2).strip()
        return f"Part {num} {label} — {parent_stem}"
    return f"{stem} — {parent_stem}"


def fix_one(syn_path: Path, is_part: bool, parent_stem: str | None) -> bool:
    """Met à jour le Title du .synthesia. Retourne True si modifié."""
    try:
        tree = ET.parse(syn_path)
    except ET.ParseError:
        return False
    root = tree.getroot()
    song = root.find(".//Song")
    if song is None:
        return False

    new_title = title_from_filename(syn_path.stem, is_part, parent_stem)
    if song.get("Title") == new_title:
        return False
    song.set("Title", new_title)

    # Réécrit avec déclaration XML + indentation
    ET.indent(root, space="  ")
    xml_bytes = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    syn_path.write_bytes(xml_bytes + b"\n")
    return True


def main() -> None:
    updated_full = 0
    updated_parts = 0
    skipped = 0

    # Niveau racine : fichiers complets
    for syn in ROOT.glob("*.synthesia"):
        if fix_one(syn, is_part=False, parent_stem=None):
            updated_full += 1
        else:
            skipped += 1

    # Sous-dossiers : parts. Le parent_stem est le nom du sous-dossier.
    for sub in sorted(ROOT.iterdir()):
        if not sub.is_dir():
            continue
        parent_stem = sub.name
        for syn in sub.glob("*.synthesia"):
            if fix_one(syn, is_part=True, parent_stem=parent_stem):
                updated_parts += 1
            else:
                skipped += 1

    print(f"✓ {updated_full} titres complets mis à jour")
    print(f"✓ {updated_parts} titres de parts mis à jour")
    if skipped:
        print(f"  ({skipped} déjà à jour ou ignorés)")


if __name__ == "__main__":
    main()
