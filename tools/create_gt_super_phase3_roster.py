#!/usr/bin/env python3
"""Phase 3: insert a small custom GT/Super roster using native Webfoot layout.

Phase 2's DragonByteZ extractor established the exact Buu's Fury format. This
script writes kind-0 (uncompressed) graphics containers, one 64x64 8bpp piece
per target structure, and redirects every non-null frame pointer in that
structure's native animation tables to the new static frame.

Default mappings are deliberately conservative and use supplied single-
character images:

    Goku GT structure <- GOKU SSJ4.png
    Trunks structure  <- FUTURE TRUNKS DBS.png
    Super Buu slot    <- BEERUS DBS.png
    Pikkon slot       <- HIT.png

Animation timing and hitboxes remain native. The image is static for every
frame/direction in this phase; this avoids corrupting the game while the next
phase can add multiple source frames per action.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
ROM_BASE = 0x08000000
OBJ_PALETTE_OFFSET = 0x0005652C
CHARACTER_TABLE_OFFSET = 0x006B6BDC
CHARACTER_TABLE_COUNT = 297

NATIVE_POINTER_PATCHES = (
    (0x006B6D80, 0x086AD1CC, 0x086AD278, "Goku slot -> Goku GT"),
    (0x006B6D6C, 0x086ACE80, 0x086AC9B8, "Mystic Gohan slot -> Gogeta"),
    (0x006B7010, 0x086B58D4, 0x086B5CE0, "Vegita slot -> Vegito"),
)

TARGETS = (
    ("GOKU_GT", "new_assets/GOKU SSJ4.png", 0x086AD278, "Goku GT"),
    ("TRUNKS_DBS", "new_assets/FUTURE TRUNKS DBS.png", 0x086B500C, "Trunks"),
    ("BEERUS", "new_assets/BEERUS DBS.png", 0x086AA2F0, "Super Buu"),
)


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def read_u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def write_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value)


def gba_palette(raw: bytes) -> list[tuple[int, int, int]]:
    result = []
    for offset in range(0, 512, 2):
        value = int.from_bytes(raw[offset : offset + 2], "little")
        r = value & 0x1F
        g = (value >> 5) & 0x1F
        b = (value >> 10) & 0x1F
        result.append(
            ((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2))
        )
    return result


def distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def remove_edge_background(image: Image.Image, tolerance: int = 42) -> Image.Image:
    """Make a solid background transparent without deleting enclosed pixels."""
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getextrema() != (255, 255):
        return image

    rgb = image.convert("RGB")
    px = rgb.load()
    width, height = image.size
    seeds = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
    seed = min(seeds, key=lambda p: sum(px[p[0], p[1]]))
    bg = px[seed[0], seed[1]]
    threshold = tolerance * tolerance
    transparent: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque(seeds)
    seen: set[tuple[int, int]] = set()
    while queue:
        x, y = queue.popleft()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        seen.add((x, y))
        r, g, b = px[x, y]
        green_background = g > 80 and g > r * 1.25 and g > b * 1.10
        if distance(px[x, y], bg) > threshold and not green_background:
            continue
        transparent.add((x, y))
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    output = image.copy()
    output_alpha = output.getchannel("A")
    for x, y in transparent:
        output_alpha.putpixel((x, y), 0)
    output.putalpha(output_alpha)
    return output


def fit_asset(path: Path) -> Image.Image:
    image = remove_edge_background(Image.open(path))
    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail((60, 60), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((64 - image.width) // 2, (64 - image.height) // 2))
    return canvas


def map_to_palette(image: Image.Image, palette: list[tuple[int, int, int]]) -> tuple[list[int], Image.Image]:
    indices: list[int] = []
    for r, g, b, a in image.getdata():
        if a < 128:
            indices.append(0)
        else:
            # Palette entry 0 is transparency; entry 1 is also black in the
            # base palette and therefore preserves opaque near-black pixels.
            indices.append(min(range(1, 256), key=lambda i: distance((r, g, b), palette[i])))
    preview = Image.new("P", (64, 64))
    preview.putpalette([component for color in palette for component in color])
    preview.putdata(indices)
    return indices, preview


def linear_tiles(indices: list[int]) -> bytes:
    raw = bytearray()
    for tile_y in range(0, 64, 8):
        for tile_x in range(0, 64, 8):
            for y in range(8):
                start = (tile_y + y) * 64 + tile_x
                raw.extend(indices[start : start + 8])
    return bytes(raw)


def ips_patch(original: bytes, modified: bytes) -> bytes:
    output = bytearray(b"PATCH")
    position = 0
    while position < len(modified):
        if position < len(original) and original[position] == modified[position]:
            position += 1
            continue
        start = position
        position += 1
        while position < len(modified) and position - start < 0xFFFF:
            if position < len(original) and original[position] == modified[position]:
                break
            position += 1
        chunk = modified[start:position]
        output.extend(start.to_bytes(3, "big"))
        output.extend(len(chunk).to_bytes(2, "big"))
        output.extend(chunk)
    output.extend(b"EOF")
    output.extend(len(modified).to_bytes(3, "big"))
    return bytes(output)


def table_values(rom: bytes) -> list[int]:
    return [
        read_u32(rom, CHARACTER_TABLE_OFFSET + index * 4)
        for index in range(CHARACTER_TABLE_COUNT)
    ]


def collect_animation_tables(rom: bytes, structure_va: int) -> list[int]:
    values = sorted({value for value in table_values(rom) if ROM_BASE <= value < ROM_BASE + len(rom)})
    next_va = min((value for value in values if value > structure_va), default=ROM_BASE + len(rom))
    structure = structure_va - ROM_BASE
    end = next_va - ROM_BASE
    start = structure + 0x54
    tables: list[int] = []
    for offset in range(start, end, 4):
        value = read_u32(rom, offset)
        if not (ROM_BASE <= value < ROM_BASE + len(rom)):
            continue
        animation = value - ROM_BASE
        if animation + 4 > len(rom):
            continue
        frame_count = read_u32(rom, animation)
        if 1 <= frame_count <= 64 and animation + 4 + frame_count * 16 <= len(rom):
            tables.append(animation)
    return list(dict.fromkeys(tables))


def make_frame(frame_va: int, container_va: int) -> bytes:
    # One 64x64 8bpp square OBJ, placed above/left of the actor origin.
    x, y = -32, -56
    record = bytearray(struct.pack("<I", 1))
    record.extend(bytes([x & 0xFF, y & 0xFF, 64, 64, x & 0xFF, y & 0xFF, 64, 64]))
    record.extend(struct.pack("<I", 0xC0002000))  # 8bpp + square + 64x64
    record.extend(struct.pack("<I", container_va))
    return bytes(record)


@dataclass
class InsertedAsset:
    label: str
    source: str
    structure_va: int
    structure_label: str
    container_offset: int
    frame_offset: int
    animation_tables: list[int]
    redirected: int


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("patch_output/DBZ_Buus_Fury_GT_Super_phase3_roster"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    base_path = root / "rom_base" / "DBZ_Buus_Fury_USA.gba"
    prefix = args.output_prefix if args.output_prefix.is_absolute() else root / args.output_prefix
    original = base_path.read_bytes()
    base_sha1 = hashlib.sha1(original).hexdigest()
    if base_sha1 != BASE_SHA1:
        raise SystemExit(f"SHA-1 inesperado: {base_sha1}")

    modified = bytearray(original)
    log: list[str] = []
    for offset, old, new, label in NATIVE_POINTER_PATCHES:
        current = read_u32(modified, offset)
        if current != old:
            raise SystemExit(f"Precondición fallida en 0x{offset:06X}")
        write_u32(modified, offset, new)
        log.append(f"0x{offset:06X}: {label}, 0x{old:08X} -> 0x{new:08X}")

    # Development title, while keeping the original ROM header checksums and
    # game code intact.
    modified[0xA0 : 0xAC] = b"DBZGTSPHASE3"

    palette = gba_palette(original[OBJ_PALETTE_OFFSET : OBJ_PALETTE_OFFSET + 512])
    inserted: list[InsertedAsset] = []
    previews = prefix.parent / (prefix.name + "_previews")
    previews.mkdir(parents=True, exist_ok=True)

    for label, source_name, structure_va, structure_label in TARGETS:
        source = root / source_name
        if not source.exists():
            raise SystemExit(f"No existe el asset: {source}")
        fitted = fit_asset(source)
        indices, preview = map_to_palette(fitted, palette)
        raw = linear_tiles(indices)
        preview.save(previews / f"{label}.png")

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
        inserted.append(
            InsertedAsset(
                label,
                source_name,
                structure_va,
                structure_label,
                container_offset,
                frame_offset,
                tables,
                redirected,
            )
        )

    modified_bytes = bytes(modified)
    modified_path = prefix.with_suffix(".gba")
    ips_path = prefix.with_suffix(".ips")
    manifest_path = prefix.with_suffix(".txt")
    modified_path.parent.mkdir(parents=True, exist_ok=True)
    modified_path.write_bytes(modified_bytes)
    ips_path.write_bytes(ips_patch(original, modified_bytes))

    lines = [
        "Dragon Ball Z: Buu's Fury USA — GT/Super Phase 3 roster",
        "===========================================================",
        "",
        f"Base SHA-1: {base_sha1}",
        f"Modified SHA-1: {hashlib.sha1(modified_bytes).hexdigest()}",
        f"Base size: {len(original)} bytes",
        f"Modified size: {len(modified_bytes)} bytes",
        f"Native object palette: file 0x{OBJ_PALETTE_OFFSET:06X}",
        "",
        "Native table mappings:",
        *[f"- {entry}" for entry in log],
        "",
        "Inserted static frames:",
    ]
    for asset in inserted:
        lines.extend(
            [
                f"- {asset.label}: {asset.source} -> {asset.structure_label} "
                f"(structure VA 0x{asset.structure_va:08X})",
                f"  container file 0x{asset.container_offset:06X}, "
                f"frame record file 0x{asset.frame_offset:06X}",
                f"  animation tables: {len(asset.animation_tables)}, "
                f"redirected pointers: {asset.redirected}",
            ]
        )
    lines.extend(
        [
            "",
            "The assets use native global OBJ palette indices and 64x64 8bpp",
            "kind-0 containers. Animation timing remains native; each target is",
            "static in this phase because all non-null frame pointers use one",
            "imported frame. Phase 4 can split source sheets into per-action frames.",
            "",
        ]
    )
    manifest_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {modified_path}")
    print(f"Wrote {ips_path}")
    print(f"Wrote {manifest_path}")
    print(f"Wrote previews in {previews}")
    print(f"Inserted assets: {len(inserted)}; size: {len(modified_bytes)} bytes")


if __name__ == "__main__":
    main()
