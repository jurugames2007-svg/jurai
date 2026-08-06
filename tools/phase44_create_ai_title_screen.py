#!/usr/bin/env python3
"""Phase 44: AI-assisted main title/menu screen.

Creates a GBA-native 240x160 title screen for "The Legacy of Goku 4" that
combines the original-feeling DBZ GBA title composition with Super/GT/AF rift
imagery. The AI background is used only as raw art; the final title text and
menu are manually overlaid with a pixel font for deterministic output.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "additive_content" / "title_screen" / "ai_title_background_raw.png"
OUT_DIR = ROOT / "additive_content" / "title_screen"
DOC = ROOT / "docs" / "PHASE44_AI_TITLE_SCREEN.md"
MANIFEST = OUT_DIR / "phase44_title_screen_manifest.json"
FINAL = OUT_DIR / "LOG4_title_screen_240x160.png"
BACKGROUND = OUT_DIR / "LOG4_title_background_240x160.png"
MENU = OUT_DIR / "LOG4_main_menu_240x160.png"
HEADER = ROOT / "include" / "log4_title_screen.h"
PREVIEW = ROOT / "data" / "log4_title_screen_preview.png"

FONT = {
    "A":["01110","10001","10001","11111","10001","10001","10001"],
    "B":["11110","10001","10001","11110","10001","10001","11110"],
    "C":["01111","10000","10000","10000","10000","10000","01111"],
    "D":["11110","10001","10001","10001","10001","10001","11110"],
    "E":["11111","10000","10000","11110","10000","10000","11111"],
    "F":["11111","10000","10000","11110","10000","10000","10000"],
    "G":["01111","10000","10000","10111","10001","10001","01111"],
    "H":["10001","10001","10001","11111","10001","10001","10001"],
    "I":["11111","00100","00100","00100","00100","00100","11111"],
    "J":["00001","00001","00001","00001","10001","10001","01110"],
    "K":["10001","10010","10100","11000","10100","10010","10001"],
    "L":["10000","10000","10000","10000","10000","10000","11111"],
    "M":["10001","11011","10101","10101","10001","10001","10001"],
    "N":["10001","11001","10101","10011","10001","10001","10001"],
    "O":["01110","10001","10001","10001","10001","10001","01110"],
    "P":["11110","10001","10001","11110","10000","10000","10000"],
    "Q":["01110","10001","10001","10001","10101","10010","01101"],
    "R":["11110","10001","10001","11110","10100","10010","10001"],
    "S":["01111","10000","10000","01110","00001","00001","11110"],
    "T":["11111","00100","00100","00100","00100","00100","00100"],
    "U":["10001","10001","10001","10001","10001","10001","01110"],
    "V":["10001","10001","10001","10001","01010","01010","00100"],
    "W":["10001","10001","10001","10101","10101","11011","10001"],
    "X":["10001","01010","01010","00100","01010","01010","10001"],
    "Y":["10001","01010","01010","00100","00100","00100","00100"],
    "Z":["11111","00001","00010","00100","01000","10000","11111"],
    "0":["01110","10001","10011","10101","11001","10001","01110"],
    "1":["00100","01100","00100","00100","00100","00100","01110"],
    "2":["01110","10001","00001","00010","00100","01000","11111"],
    "3":["11110","00001","00001","01110","00001","00001","11110"],
    "4":["00010","00110","01010","10010","11111","00010","00010"],
    "5":["11111","10000","10000","11110","00001","00001","11110"],
    "6":["01110","10000","10000","11110","10001","10001","01110"],
    "7":["11111","00001","00010","00100","01000","01000","01000"],
    "8":["01110","10001","10001","01110","10001","10001","01110"],
    "9":["01110","10001","10001","01111","00001","00001","01110"],
    " ":["00000","00000","00000","00000","00000","00000","00000"],
    ":":["00000","00100","00100","00000","00100","00100","00000"],
    "-":["00000","00000","00000","11111","00000","00000","00000"],
    ".":["00000","00000","00000","00000","00000","01100","01100"],
    "•":["00000","00000","00100","01110","00100","00000","00000"],
}


def draw_text(img: Image.Image, x: int, y: int, text: str, scale: int, color: tuple[int,int,int,int], shadow: tuple[int,int,int,int] | None = None) -> int:
    d = ImageDraw.Draw(img)
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        if shadow:
            for row, line in enumerate(glyph):
                for col, bit in enumerate(line):
                    if bit == "1":
                        d.rectangle((cx + col*scale + scale, y + row*scale + scale, cx + (col+1)*scale - 1 + scale, y + (row+1)*scale - 1 + scale), fill=shadow)
        for row, line in enumerate(glyph):
            for col, bit in enumerate(line):
                if bit == "1":
                    d.rectangle((cx + col*scale, y + row*scale, cx + (col+1)*scale - 1, y + (row+1)*scale - 1), fill=color)
        cx += 6 * scale
    return cx - x


def text_width(text: str, scale: int) -> int:
    return len(text) * 6 * scale


def centered(img: Image.Image, y: int, text: str, scale: int, color, shadow=None) -> None:
    x = (240 - text_width(text, scale)) // 2
    draw_text(img, x, y, text, scale, color, shadow)


def make_background() -> Image.Image:
    if not RAW.exists():
        raise SystemExit(f"Missing raw AI title background: {RAW}")
    raw = Image.open(RAW).convert("RGBA")
    # Raw is 4:3. Crop to GBA 3:2 while keeping portals/clouds.
    w, h = raw.size
    target_ratio = 240 / 160
    crop_h = int(w / target_ratio)
    if crop_h <= h:
        y0 = max(0, (h - crop_h) // 2)
        raw = raw.crop((0, y0, w, y0 + crop_h))
    else:
        crop_w = int(h * target_ratio)
        x0 = max(0, (w - crop_w) // 2)
        raw = raw.crop((x0, 0, x0 + crop_w, h))
    bg = raw.resize((240, 160), Image.Resampling.NEAREST)
    # Dark central field for title readability.
    overlay = Image.new("RGBA", (240, 160), (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    d.rectangle((24, 40, 216, 111), fill=(0,0,20,120))
    d.rectangle((30, 45, 210, 106), outline=(255,210,64,170))
    return Image.alpha_composite(bg, overlay)


def quantize_gba(img: Image.Image) -> Image.Image:
    return img.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGBA")


def make_title() -> tuple[Image.Image, Image.Image]:
    bg = make_background()
    title = bg.copy()
    # Dragon Ball-ish title colors without using original logo art.
    centered(title, 46, "THE LEGACY", 3, (255, 238, 104, 255), (98, 22, 18, 255))
    centered(title, 70, "OF GOKU 4", 3, (255, 255, 255, 255), (40, 72, 180, 255))
    centered(title, 98, "SUPER  GT  AF", 2, (126, 226, 255, 255), (14, 20, 44, 255))
    centered(title, 137, "PRESS START", 1, (255, 232, 120, 255), (0, 0, 0, 255))
    menu = title.copy()
    d = ImageDraw.Draw(menu)
    d.rectangle((55, 121, 185, 154), fill=(18, 42, 44, 210), outline=(250, 222, 90, 255))
    draw_text(menu, 67, 126, "NEW GAME", 1, (255,255,255,255), (0,0,0,255))
    draw_text(menu, 67, 138, "CONTINUE", 1, (190,230,255,255), (0,0,0,255))
    draw_text(menu, 132, 126, "RIFT", 1, (255,100,80,255), (0,0,0,255))
    draw_text(menu, 132, 138, "GATE", 1, (255,232,120,255), (0,0,0,255))
    return quantize_gba(title), quantize_gba(menu)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bg = make_background()
    bg_q = quantize_gba(bg)
    title, menu = make_title()
    bg_q.save(BACKGROUND, optimize=True)
    title.save(FINAL, optimize=True)
    menu.save(MENU, optimize=True)
    manifest = {
        "schema": "jurai.phase44.ai_title_screen.v1",
        "policy": "ai_background_plus_manual_pixel_text_native_gba_dimensions",
        "raw_source": RAW.relative_to(ROOT).as_posix(),
        "background": BACKGROUND.relative_to(ROOT).as_posix(),
        "title_screen": FINAL.relative_to(ROOT).as_posix(),
        "main_menu_screen": MENU.relative_to(ROOT).as_posix(),
        "dimensions": [240,160],
        "palette_limit": 128,
        "sha1": {
            "title_screen": hashlib.sha1(FINAL.read_bytes()).hexdigest(),
            "main_menu_screen": hashlib.sha1(MENU.read_bytes()).hexdigest(),
        },
        "notes": ["Menu is an image asset/payload candidate; runtime title hook is future work.", "Text is manually overlaid with deterministic pixel font."],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Phase 44 — AI-assisted title screen\n\n"
        "Generated a GBA-native 240×160 title/menu screen for **The Legacy of Goku 4** using an AI background plus manual pixel-font title overlay.\n\n"
        f"- Background: `{BACKGROUND.relative_to(ROOT)}`\n"
        f"- Title: `{FINAL.relative_to(ROOT)}`\n"
        f"- Main menu: `{MENU.relative_to(ROOT)}`\n"
        f"- Manifest: `{MANIFEST.relative_to(ROOT)}`\n\n"
        "This is not hooked into the ROM title flow yet; it is ready as a native-dimension title asset.\n",
        encoding="utf-8",
    )
    print(f"Wrote {FINAL}")
    print(f"Wrote {MENU}")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
