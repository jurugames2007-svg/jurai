#!/usr/bin/env python3
"""Build the small 240x160 Mode 4 scene used by the libgba demo.

The script deliberately converts source images into one indexed framebuffer.
It is not a ROM extractor: it only prepares user-supplied PNG/JPEG art for the
standalone demo. Pillow is needed only when regenerating the checked-in header.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

WIDTH = 240
HEIGHT = 160

# These entries are first in the palette and are used by main.c for UI drawing.
UI_COLORS = [
    (0, 0, 0),          # 0 SCENE_COL_BLACK
    (255, 255, 255),    # 1 SCENE_COL_WHITE
    (255, 220, 0),      # 2 SCENE_COL_YELLOW
    (0, 240, 255),      # 3 SCENE_COL_CYAN
    (255, 70, 70),      # 4 SCENE_COL_RED
    (0, 255, 110),      # 5 SCENE_COL_GREEN
    (13, 25, 66),       # 6 SCENE_COL_NAVY
    (255, 130, 0),      # 7 SCENE_COL_ORANGE
    (180, 40, 220),     # 8 SCENE_COL_PURPLE
    (80, 80, 100),      # 9 SCENE_COL_GRAY
    (40, 130, 210),     # 10 SCENE_COL_BLUE
    (255, 140, 190),    # 11 SCENE_COL_PINK
    (120, 65, 30),      # 12 SCENE_COL_BROWN
    (180, 180, 180),    # 13 SCENE_COL_LIGHT_GRAY
    (100, 0, 100),      # 14 SCENE_COL_MAGENTA
    (0, 120, 120),      # 15 SCENE_COL_TEAL
]

ROSTER = [
    ("GOKU SSJ4", "GOKU SSJ4.png"),
    ("TRUNKS DBS", "FUTURE TRUNKS DBS.png"),
    ("GOKU", "GOKU ABSALON.png"),
    ("BEERUS", "BEERUS DBS.png"),
    ("HIT", "HIT.png"),
    ("RILDO GT", "GENERAL RILDO GT.png"),
]


def rgb5(r: int, g: int, b: int) -> int:
    """Convert 8-bit RGB to the GBA's 15-bit BGR555 palette word."""
    return ((r >> 3) & 0x1F) | (((g >> 3) & 0x1F) << 5) | (((b >> 3) & 0x1F) << 10)


def make_background() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), UI_COLORS[6])
    draw = ImageDraw.Draw(image)

    # Horizontal bands keep the screen readable even when source art has a
    # very bright or very dark background.
    for y in range(HEIGHT):
        r = 15 + (y * 18 // HEIGHT)
        g = 20 + (y * 15 // HEIGHT)
        b = 70 + (y * 35 // HEIGHT)
        draw.line((0, y, WIDTH, y), fill=(r, g, b))

    draw.rectangle((0, 0, WIDTH - 1, 21), fill=UI_COLORS[6])
    draw.rectangle((0, 136, WIDTH - 1, HEIGHT - 1), fill=UI_COLORS[6])
    draw.rectangle((0, 22, WIDTH - 1, 23), fill=UI_COLORS[3])
    draw.rectangle((0, 134, WIDTH - 1, 135), fill=UI_COLORS[3])
    return image


def load_card(path: Path, width: int, height: int) -> Image.Image:
    source = Image.open(path).convert("RGBA")
    # Nearest-neighbour preserves the pixel-art edges in the submitted assets.
    source.thumbnail((width - 4, height - 4), Image.Resampling.NEAREST)
    card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    x = (width - source.width) // 2
    y = (height - source.height) // 2
    card.alpha_composite(source, (x, y))
    return card


def make_scene(asset_dir: Path) -> Image.Image:
    image = make_background().convert("RGBA")
    draw = ImageDraw.Draw(image)
    card_w, card_h = 72, 54
    positions = [(4, 26), (82, 26), (160, 26), (4, 88), (82, 88), (160, 88)]
    accents = [UI_COLORS[2], UI_COLORS[3], UI_COLORS[7], UI_COLORS[5], UI_COLORS[8], UI_COLORS[11]]

    for (label, filename), (x, y), accent in zip(ROSTER, positions, accents):
        draw.rectangle((x, y, x + card_w - 1, y + card_h - 1), fill=(4, 8, 25, 255), outline=accent)
        source = asset_dir / filename
        if source.exists():
            card = load_card(source, card_w - 4, card_h - 13)
            image.alpha_composite(card, (x + 2, y + 2))
        # Labels are also drawn by the GBA font at runtime. This small label is
        # useful in the preview PNG before the ROM is built.
        draw.text((x + 3, y + card_h - 10), label, fill=UI_COLORS[1])

    draw.text((8, 3), "DBZ BUUS FURY", fill=UI_COLORS[2])
    draw.text((8, 15), "GT / SUPER LAB", fill=UI_COLORS[1])
    draw.text((6, 140), "MODE 4 DEMO / VBLANK", fill=UI_COLORS[1])
    return image.convert("RGB")


def palette_for(image: Image.Image) -> list[tuple[int, int, int]]:
    # Ask Pillow for the remaining colors, then reserve the first 16 entries
    # for stable UI colors used in C.
    reduced = image.quantize(colors=240, method=Image.Quantize.MEDIANCUT)
    raw = reduced.getpalette()[: 240 * 3]
    colors: list[tuple[int, int, int]] = []
    for i in range(0, len(raw), 3):
        color = tuple(raw[i : i + 3])
        if color not in UI_COLORS and color not in colors:
            colors.append(color)

    result = UI_COLORS + colors[: 256 - len(UI_COLORS)]
    result.extend([(0, 0, 0)] * (256 - len(result)))
    return result[:256]


def indexed_pixels(image: Image.Image, palette: list[tuple[int, int, int]]) -> bytes:
    palette_image = Image.new("P", (16, 16))
    flattened: list[int] = []
    for r, g, b in palette:
        flattened.extend((r, g, b))
    palette_image.putpalette(flattened)
    indexed = image.quantize(palette=palette_image, dither=Image.Dither.NONE)
    return indexed.tobytes()


def write_header(output: Path, palette: list[tuple[int, int, int]], pixels: bytes) -> None:
    words = [rgb5(*color) for color in palette]
    with output.open("w", encoding="utf-8") as handle:
        handle.write("/* Generated by tools/build_demo_assets.py. Do not edit by hand. */\n")
        handle.write("#ifndef GENERATED_SCENE_H\n#define GENERATED_SCENE_H\n\n")
        handle.write("#define SCENE_WIDTH 240\n#define SCENE_HEIGHT 160\n\n")
        handle.write("#define SCENE_COL_BLACK 0\n")
        handle.write("#define SCENE_COL_WHITE 1\n")
        handle.write("#define SCENE_COL_YELLOW 2\n")
        handle.write("#define SCENE_COL_CYAN 3\n")
        handle.write("#define SCENE_COL_RED 4\n")
        handle.write("#define SCENE_COL_GREEN 5\n")
        handle.write("#define SCENE_COL_NAVY 6\n")
        handle.write("#define SCENE_COL_ORANGE 7\n")
        handle.write("#define SCENE_COL_PURPLE 8\n")
        handle.write("#define SCENE_COL_GRAY 9\n")
        handle.write("#define SCENE_COL_BLUE 10\n")
        handle.write("#define SCENE_COL_PINK 11\n")
        handle.write("#define SCENE_COL_BROWN 12\n")
        handle.write("#define SCENE_COL_LIGHT_GRAY 13\n")
        handle.write("#define SCENE_COL_MAGENTA 14\n")
        handle.write("#define SCENE_COL_TEAL 15\n\n")
        handle.write("static const unsigned short generated_scene_palette[256] __attribute__((aligned(4))) = {\n")
        for start in range(0, 256, 8):
            row = ", ".join(f"0x{value:04X}" for value in words[start : start + 8])
            handle.write(f"    {row}{',' if start + 8 < 256 else ''}\n")
        handle.write("};\n\n")
        handle.write("static const unsigned char generated_scene_bitmap[240 * 160] __attribute__((aligned(4))) = {\n")
        for start in range(0, len(pixels), 24):
            row = ", ".join(str(value) for value in pixels[start : start + 24])
            handle.write(f"    {row}{',' if start + 24 < len(pixels) else ''}\n")
        handle.write("};\n\n#endif\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, default=Path("new_assets"))
    parser.add_argument("--header", type=Path, default=Path("include/generated_scene.h"))
    parser.add_argument("--preview", type=Path, default=Path("data/scene_preview.png"))
    args = parser.parse_args()

    scene = make_scene(args.assets)
    palette = palette_for(scene)
    pixels = indexed_pixels(scene, palette)

    args.header.parent.mkdir(parents=True, exist_ok=True)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    scene.save(args.preview)
    write_header(args.header, palette, pixels)
    print(f"Wrote {args.header} ({len(pixels)} pixels, 256-color palette)")
    print(f"Wrote {args.preview}")


if __name__ == "__main__":
    main()
