#!/usr/bin/env python3
"""Create a reversible first-pass GT/Super patch for the verified USA dump.

This phase deliberately reuses character definitions already present in the
Buu's Fury ROM. It changes three character-table entries without guessing the
custom Webfoot sprite compressor used by the attached PNG sheets:

* Goku      -> the native Goku (GT) definition
* Mystic Gohan -> the native Gogeta definition
* Vegita    -> the native Vegito definition

The custom GT/Super sheets are retained in new_assets/ and will be converted in
phase 2 after the per-frame Webfoot graphics codec is handled. Replacing a
sprite table pointer with a same-format native definition is much safer than
writing arbitrary 4bpp data into the game.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
ROM_BASE = 0x08000000

# File offsets from the exact USA dump's character pointer table.
PATCHES = [
    {
        "name": "Goku slot -> native Goku GT",
        "offset": 0x6B6D80,
        "old": 0x086AD1CC,
        "new": 0x086AD278,
    },
    {
        "name": "Mystic Gohan slot -> native Gogeta",
        "offset": 0x6B6D6C,
        "old": 0x086ACE80,
        "new": 0x086AC9B8,
    },
    {
        "name": "Vegita slot -> native Vegito",
        "offset": 0x6B7010,
        "old": 0x086B58D4,
        "new": 0x086B5CE0,
    },
]


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def ips_patch(original: bytes, modified: bytes) -> bytes:
    """Write a compact IPS patch for ordinary non-overlapping byte changes."""
    if len(original) != len(modified):
        raise ValueError("IPS generator expects ROMs of equal length")

    out = bytearray(b"PATCH")
    i = 0
    while i < len(original):
        if original[i] == modified[i]:
            i += 1
            continue
        start = i
        while i < len(original) and original[i] != modified[i] and i - start < 0xFFFF:
            i += 1
        chunk = modified[start:i]
        if start > 0xFFFFFF:
            raise ValueError("IPS offset exceeds 24-bit range")
        out.extend(start.to_bytes(3, "big"))
        out.extend(len(chunk).to_bytes(2, "big"))
        out.extend(chunk)
    out.extend(b"EOF")
    return bytes(out)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    base_path = root / "rom_base" / "DBZ_Buus_Fury_USA.gba"
    output_dir = root / "patch_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    modified_path = output_dir / "DBZ_Buus_Fury_GT_Super_phase1.gba"
    patch_path = output_dir / "DBZ_Buus_Fury_GT_Super_phase1.ips"
    manifest_path = output_dir / "DBZ_Buus_Fury_GT_Super_phase1.txt"

    original = base_path.read_bytes()
    actual_sha1 = sha1(original)
    if actual_sha1 != BASE_SHA1:
        raise SystemExit(
            f"ROM no coincide con el dump USA esperado: {actual_sha1} != {BASE_SHA1}"
        )

    modified = bytearray(original)
    applied: list[str] = []
    for patch in PATCHES:
        offset = patch["offset"]
        old = struct.pack("<I", patch["old"])
        new = struct.pack("<I", patch["new"])
        actual = bytes(modified[offset : offset + 4])
        if actual != old:
            raise SystemExit(
                f"Precondicion no valida en 0x{offset:06X}: "
                f"{actual.hex()} != {old.hex()}"
            )
        modified[offset : offset + 4] = new
        applied.append(
            f"{patch['name']}: file 0x{offset:06X}, "
            f"{patch['old']:08X} -> {patch['new']:08X}"
        )

    # Put an unambiguous development title in the GBA header. This does not
    # change gameplay and makes the generated test ROM easy to identify.
    title_offset = 0xA0
    old_title = bytes(modified[title_offset : title_offset + 12])
    new_title = b"DBZGTSPHACK1"
    modified[title_offset : title_offset + 12] = new_title
    applied.append(f"GBA title: {old_title.rstrip(bytes([0])).decode('ascii', 'replace')} -> {new_title.decode('ascii')}")

    modified_bytes = bytes(modified)
    modified_path.write_bytes(modified_bytes)
    patch_path.write_bytes(ips_patch(original, modified_bytes))
    manifest_path.write_text(
        "Dragon Ball Z: Buu's Fury USA - GT/Super phase 1\n"
        f"Base SHA-1: {actual_sha1}\n"
        f"Modified SHA-1: {sha1(modified_bytes)}\n"
        "\nApplied changes:\n- "
        + "\n- ".join(applied)
        + "\n\n"
        "This phase reuses native same-format character definitions. The custom\n"
        "PNG/JPEG sheets are not blindly copied into the ROM; phase 2 must\n"
        "encode each animation frame with Webfoot's custom graphics codec.\n",
        encoding="utf-8",
    )
    print(f"Wrote {modified_path}")
    print(f"Wrote {patch_path}")
    print(f"Wrote {manifest_path}")
    print(f"Base SHA-1: {actual_sha1}")
    print(f"Modified SHA-1: {sha1(modified_bytes)}")


if __name__ == "__main__":
    main()
