#!/usr/bin/env python3
"""Import a custom Webfoot-compatible character frame into Buu's Fury.

Phase 2 established the real format with DragonByteZ:

    character structure -> animation table -> Buu frame record ->
    graphics container -> 8bpp tile bytes

This phase uses an uncompressed Webfoot container (kind 0), which the original
engine already supports, so it can insert a safe first custom frame without
having to reproduce the game's bitstream compressor. All animation frame
pointers of the native Goku (GT) definition are redirected to one custom 64x64
frame. The animation timing remains native; the image is intentionally static
until multiple custom frames are supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

from PIL import Image, ImageOps

BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
ROM_BASE = 0x08000000
OBJ_PALETTE_OFFSET = 0x0005652C
CHARACTER_TABLE_OFFSET = 0x006B6D80
GOKU_GT_STRUCTURE_VA = 0x086AD278
GOKU_GT_STRUCTURE_OFFSET = GOKU_GT_STRUCTURE_VA - ROM_BASE

# Native phase-1 compatibility mappings.
NATIVE_POINTER_PATCHES = (
    (0x006B6D80, 0x086AD1CC, 0x086AD278, "Goku slot -> Goku GT"),
    (0x006B6D6C, 0x086ACE80, 0x086AC9B8, "Mystic Gohan slot -> Gogeta"),
    (0x006B7010, 0x086B58D4, 0x086B5CE0, "Vegita slot -> Vegito"),
)


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def gba_rgb555_palette(data: bytes) -> list[tuple[int, int, int]]:
    palette = []
    for offset in range(0, 512, 2):
        value = int.from_bytes(data[offset : offset + 2], "little")
        palette.append(
            (
                ((value & 0x1F) << 3) | ((value & 0x1F) >> 2),
                (((value >> 5) & 0x1F) << 3) | (((value >> 5) & 0x1F) >> 2),
                (((value >> 10) & 0x1F) << 3) | (((value >> 10) & 0x1F) >> 2),
            )
        )
    return palette


def nearest_palette_index(
    rgb: tuple[int, int, int], palette: list[tuple[int, int, int]]
) -> int:
    r, g, b = rgb
    best_index = 1
    best_distance = 1 << 60
    for index in range(1, len(palette)):
        pr, pg, pb = palette[index]
        distance = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if distance < best_distance:
            best_index = index
            best_distance = distance
    return best_index


def fit_to_64(source: Image.Image) -> Image.Image:
    source = source.convert("RGBA")
    alpha = source.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        source = source.crop(bbox)
    source.thumbnail((60, 60), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.alpha_composite(
        source,
        ((64 - source.width) // 2, (64 - source.height) // 2),
    )
    return canvas


def quantize_to_gba_indices(
    image: Image.Image, palette: list[tuple[int, int, int]]
) -> tuple[list[int], Image.Image]:
    pixels: list[int] = []
    for r, g, b, a in image.getdata():
        pixels.append(0 if a < 128 else nearest_palette_index((r, g, b), palette))

    preview = Image.new("P", (64, 64))
    flat_palette = [component for color in palette for component in color]
    preview.putpalette(flat_palette)
    preview.putdata(pixels)
    return pixels, preview


def tile_linearize(pixels: list[int], width: int = 64, height: int = 64) -> bytes:
    """Encode 8bpp GBA tiles in the game's row-major tile order."""
    raw = bytearray()
    for tile_y in range(0, height, 8):
        for tile_x in range(0, width, 8):
            for y in range(8):
                row = (tile_y + y) * width + tile_x
                raw.extend(pixels[row : row + 8])
    return bytes(raw)


def ips_patch(original: bytes, modified: bytes) -> bytes:
    """Create an IPS patch, including the optional final-size record."""
    out = bytearray(b"PATCH")
    position = 0
    while position < len(modified):
        original_value = original[position] if position < len(original) else None
        if original_value is not None and original_value == modified[position]:
            position += 1
            continue
        start = position
        position += 1
        while position < len(modified) and position - start < 0xFFFF:
            if position < len(original) and original[position] == modified[position]:
                break
            position += 1
        chunk = modified[start:position]
        if start > 0xFFFFFF:
            raise ValueError("IPS offset exceeds 24-bit range")
        out.extend(start.to_bytes(3, "big"))
        out.extend(len(chunk).to_bytes(2, "big"))
        out.extend(chunk)
    out.extend(b"EOF")
    if len(modified) <= 0xFFFFFF:
        out.extend(len(modified).to_bytes(3, "big"))
    return bytes(out)


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def write_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value)


def patch_native_mappings(rom: bytearray, log: list[str]) -> None:
    for offset, old, new, label in NATIVE_POINTER_PATCHES:
        current = read_u32(rom, offset)
        if current != old:
            raise ValueError(
                f"precondicion fallida en 0x{offset:06X}: "
                f"0x{current:08X} != 0x{old:08X}"
            )
        write_u32(rom, offset, new)
        log.append(f"0x{offset:06X}: {label} (0x{old:08X} -> 0x{new:08X})")


def collect_animation_tables(rom: bytes) -> list[int]:
    """Read the pointer run in the native Goku GT structure.

    The structure ends immediately before the next alphabetical character
    structure at 0x06AD30C. The animation pointer run starts at +0x54.
    """
    start = GOKU_GT_STRUCTURE_OFFSET + 0x54
    end = 0x006AD30C
    pointers: list[int] = []
    for offset in range(start, end, 4):
        value = read_u32(rom, offset)
        if value == 0:
            continue
        if not (ROM_BASE <= value < ROM_BASE + len(rom)):
            continue
        animation = value - ROM_BASE
        if animation + 4 > len(rom):
            continue
        frame_count = read_u32(rom, animation)
        if 1 <= frame_count <= 64 and animation + 4 + frame_count * 16 <= len(rom):
            pointers.append(animation)
    return list(dict.fromkeys(pointers))


def make_custom_frame(
    frame_va: int, container_va: int, x: int = -32, y: int = -56
) -> bytes:
    if not -128 <= x <= 127 or not -128 <= y <= 127:
        raise ValueError("frame origin must fit in the game's signed byte fields")
    # One 64x64, 8bpp, square OBJ piece. Bytes 2..7 mirror the native x/y and
    # dimensions; the game renderer uses the OBJ attributes at +8 and pointer
    # at +12, while retaining the duplicated fields is safest for tools.
    record = bytearray()
    record.extend(struct.pack("<I", 1))
    record.extend(
        bytes(
            [
                x & 0xFF,
                y & 0xFF,
                64,
                64,
                x & 0xFF,
                y & 0xFF,
                64,
                64,
            ]
        )
    )
    # attr0: 8bpp (bit 13), square shape; attr1: 64x64 (size 3).
    record.extend(struct.pack("<I", 0xC0002000))
    record.extend(struct.pack("<I", container_va))
    return bytes(record)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asset",
        type=Path,
        default=Path("new_assets/GOKU SSJ4.png"),
        help="RGBA source image; default is the attached Goku SSJ4 image",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("patch_output/DBZ_Buus_Fury_GT_Super_phase3_GokuSSJ4"),
    )
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    base_path = root / "rom_base" / "DBZ_Buus_Fury_USA.gba"
    asset_path = args.asset if args.asset.is_absolute() else root / args.asset
    prefix = args.output_prefix if args.output_prefix.is_absolute() else root / args.output_prefix

    original = base_path.read_bytes()
    actual_sha1 = hashlib.sha1(original).hexdigest()
    if actual_sha1 != BASE_SHA1:
        raise SystemExit(f"SHA-1 de base no esperado: {actual_sha1}")
    if not asset_path.exists():
        raise SystemExit(f"asset no encontrado: {asset_path}")

    palette = gba_rgb555_palette(original[OBJ_PALETTE_OFFSET : OBJ_PALETTE_OFFSET + 512])
    fitted = fit_to_64(Image.open(asset_path))
    indices, preview = quantize_to_gba_indices(fitted, palette)
    raw_graphics = tile_linearize(indices)

    preview_path = args.preview
    if preview_path is None:
        preview_path = prefix.with_name(prefix.name + "_preview.png")
    if not preview_path.is_absolute():
        preview_path = root / preview_path
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview.save(preview_path)

    modified = bytearray(original)
    log: list[str] = []
    patch_native_mappings(modified, log)

    container_offset = align(len(modified), 0x100)
    if container_offset > len(modified):
        modified.extend(b"\xFF" * (container_offset - len(modified)))
    container_va = ROM_BASE + container_offset
    container = struct.pack("<II", 0, len(raw_graphics)) + raw_graphics
    modified.extend(container)

    frame_offset = align(len(modified), 4)
    if frame_offset > len(modified):
        modified.extend(b"\xFF" * (frame_offset - len(modified)))
    frame_va = ROM_BASE + frame_offset
    modified.extend(make_custom_frame(frame_va, container_va))

    animation_tables = collect_animation_tables(original)
    redirected = 0
    animation_details: list[str] = []
    for animation_offset in animation_tables:
        frame_count = read_u32(original, animation_offset)
        changed = 0
        for index in range(frame_count * 4):
            pointer_offset = animation_offset + 4 + index * 4
            old_pointer = read_u32(original, pointer_offset)
            if old_pointer == 0:
                continue
            write_u32(modified, pointer_offset, frame_va)
            changed += 1
        if changed:
            redirected += changed
            animation_details.append(
                f"animation 0x{animation_offset:06X}: {frame_count} frames, "
                f"{changed} directional pointers"
            )

    modified_path = prefix.with_suffix(".gba")
    ips_path = prefix.with_suffix(".ips")
    manifest_path = prefix.with_suffix(".txt")
    modified_path.parent.mkdir(parents=True, exist_ok=True)
    modified_path.write_bytes(modified)
    ips_path.write_bytes(ips_patch(original, bytes(modified)))
    manifest_path.write_text(
        "Dragon Ball Z: Buu's Fury USA — GT/Super Phase 3\n"
        "=================================================\n\n"
        f"Base SHA-1: {actual_sha1}\n"
        f"Modified SHA-1: {hashlib.sha1(modified).hexdigest()}\n"
        f"Source asset: {asset_path.relative_to(root) if asset_path.is_relative_to(root) else asset_path}\n"
        f"Palette: file 0x{OBJ_PALETTE_OFFSET:06X}, native 256-color OBJ palette\n"
        f"Graphics container: file 0x{container_offset:06X}, VA 0x{container_va:08X}\n"
        f"Graphics kind: 0 (uncompressed), payload {len(raw_graphics)} bytes\n"
        f"Custom frame record: file 0x{frame_offset:06X}, VA 0x{frame_va:08X}\n"
        f"Animation tables found: {len(animation_tables)}\n"
        f"Frame pointers redirected: {redirected}\n\n"
        "Native mappings:\n- "
        + "\n- ".join(log)
        + "\n\nAnimation tables:\n- "
        + "\n- ".join(animation_details)
        + "\n\nThe custom frame is static for this phase: original animation timing is kept, "
          "but every non-null frame pointer in Goku GT points at the same 64x64 frame.\n",
        encoding="utf-8",
    )
    print(f"Wrote {modified_path}")
    print(f"Wrote {ips_path}")
    print(f"Wrote {manifest_path}")
    print(f"Wrote {preview_path}")
    print(f"Animation tables: {len(animation_tables)}; redirected pointers: {redirected}")


if __name__ == "__main__":
    main()
