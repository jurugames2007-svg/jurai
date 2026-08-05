#!/usr/bin/env python3
"""Phase 4: native transformation-state integration.

Uses the submitted three-form Adult Goku GT sheet for the native Goku,
Super Saiyan and Super Saiyan 3 character structures, plus the phase-3 custom
Goku GT, Trunks and Beerus frames. Existing game state IDs remain intact, so
this phase changes visual forms without inventing a new save/RAM structure.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from PIL import Image

from create_gt_super_phase3_roster import (
    BASE_SHA1,
    ROM_BASE,
    OBJ_PALETTE_OFFSET,
    NATIVE_POINTER_PATCHES,
    TARGETS,
    gba_palette,
    remove_edge_background,
    map_to_palette,
    linear_tiles,
    align,
    read_u32,
    write_u32,
    collect_animation_tables,
    make_frame,
    ips_patch,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
OUTPUT_PREFIX = ROOT / "patch_output" / "DBZ_Buus_Fury_GT_Super_phase4_forms"

# Character metadata structures from the verified BG3E table.
GOKU_BASE = 0x086AD1CC
GOKU_GT = 0x086AD278
GOKU_SSJ = 0x086AD3B8
GOKU_SSJ3 = 0x086AD510

FORM_TARGETS = (
    ("GOKU_BASE", "Adult Goku GT / base form", "ADULT GOKU GT.png", (0, 0, 426, 616), GOKU_BASE),
    ("GOKU_SSJ", "Adult Goku GT / Super Saiyan", "ADULT GOKU GT.png", (426, 0, 853, 616), GOKU_SSJ),
    ("GOKU_SSJ3", "Adult Goku GT / Super Saiyan 3", "ADULT GOKU GT.png", (853, 0, 1280, 616), GOKU_SSJ3),
    ("GOKU_GT", "Goku SSJ4", "GOKU SSJ4.png", None, GOKU_GT),
    ("TRUNKS_DBS", "Future Trunks", "FUTURE TRUNKS DBS.png", None, 0x086B500C),
    ("BEERUS", "Beerus on Super Buu slot", "BEERUS DBS.png", None, 0x086AA2F0),
)


def fit_image(path: Path, crop: tuple[int, int, int, int] | None) -> Image.Image:
    image = remove_edge_background(Image.open(path))
    if crop is not None:
        image = image.crop(crop)
    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail((60, 60), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((64 - image.width) // 2, (64 - image.height) // 2))
    return canvas


def main() -> None:
    original = BASE_PATH.read_bytes()
    if hashlib.sha1(original).hexdigest() != BASE_SHA1:
        raise SystemExit("La ROM base no coincide con el SHA-1 USA esperado")

    modified = bytearray(original)
    log: list[str] = []
    for offset, old, new, label in NATIVE_POINTER_PATCHES:
        if read_u32(modified, offset) != old:
            raise SystemExit(f"Precondición fallida en 0x{offset:06X}")
        write_u32(modified, offset, new)
        log.append(f"0x{offset:06X}: {label}, 0x{old:08X} -> 0x{new:08X}")

    modified[0xA0 : 0xAC] = b"DBZGTSPHASE4"
    palette = gba_palette(original[OBJ_PALETTE_OFFSET : OBJ_PALETTE_OFFSET + 512])
    preview_dir = OUTPUT_PREFIX.parent / (OUTPUT_PREFIX.name + "_previews")
    preview_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for label, description, source_name, crop, structure_va in FORM_TARGETS:
        source = ROOT / "new_assets" / source_name
        image = fit_image(source, crop)
        indices, preview = map_to_palette(image, palette)
        preview.save(preview_dir / f"{label}.png")
        raw = linear_tiles(indices)

        container_offset = align(len(modified), 0x100)
        modified.extend(b"\xFF" * (container_offset - len(modified)))
        container_va = ROM_BASE + container_offset
        modified.extend(struct.pack("<II", 0, len(raw)))
        modified.extend(raw)

        frame_offset = align(len(modified), 4)
        modified.extend(b"\xFF" * (frame_offset - len(modified)))
        frame_va = ROM_BASE + frame_offset
        modified.extend(make_frame(frame_va, container_va))

        tables = collect_animation_tables(original, structure_va)
        redirected = 0
        for table in tables:
            count = read_u32(original, table)
            for index in range(count * 4):
                pointer_offset = table + 4 + index * 4
                if read_u32(original, pointer_offset) == 0:
                    continue
                write_u32(modified, pointer_offset, frame_va)
                redirected += 1
        results.append((label, description, source_name, structure_va, container_offset, frame_offset, len(tables), redirected))

    modified_bytes = bytes(modified)
    gba_path = OUTPUT_PREFIX.with_suffix(".gba")
    ips_path = OUTPUT_PREFIX.with_suffix(".ips")
    txt_path = OUTPUT_PREFIX.with_suffix(".txt")
    gba_path.write_bytes(modified_bytes)
    ips_path.write_bytes(ips_patch(original, modified_bytes))

    lines = [
        "Dragon Ball Z: Buu's Fury USA — GT/Super Phase 4 forms",
        "==========================================================",
        "",
        f"Base SHA-1: {BASE_SHA1}",
        f"Modified SHA-1: {hashlib.sha1(modified_bytes).hexdigest()}",
        f"Original size: {len(original)} bytes",
        f"Modified size: {len(modified_bytes)} bytes",
        "",
        "Transformation structures:",
    ]
    lines.extend(f"- {x}" for x in log)
    lines.append("")
    lines.append("Imported transformation/character frames:")
    for label, description, source_name, va, container, frame, tables, redirected in results:
        lines.append(f"- {label}: {description}")
        lines.append(f"  source: new_assets/{source_name}")
        lines.append(f"  structure VA: 0x{va:08X}; container: 0x{container:06X}; frame: 0x{frame:06X}")
        lines.append(f"  animation tables: {tables}; redirected pointers: {redirected}")
    lines.extend([
        "",
        "The existing character IDs and transformation logic are preserved.",
        "This phase uses one native-palette 64x64 frame per state; timing remains",
        "native, while action-specific frame separation remains a later step.",
    ])
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {gba_path}")
    print(f"Wrote {ips_path}")
    print(f"Wrote {txt_path}")
    print(f"Wrote previews in {preview_dir}")


if __name__ == "__main__":
    main()
