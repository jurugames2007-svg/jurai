#!/usr/bin/env python3
"""Phase 49: boot-time Gateway menu hook.

This creates a real boot hook: the first ARM branch of the GBA ROM is redirected
to appended ARM code that displays a Mode 3 Gateway menu before the original
Buu's Fury entry point. The menu lets testers move between route/dimension
screens from the very start.

Controls:
- Up/Down: select route on Gateway menu.
- A/Start on Original: boot original Buu's Fury.
- A/Start on other entries: open that route/dimension information screen.
- B on info screen: return to menu.
- Start on info screen: boot original Buu's Fury.

This is a debug/test hook. It does not yet warp into native maps; it provides a
stable runtime Gateway selector and route/dimension screens at boot.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase49_boot_gateway_menu"
DOC = ROOT / "docs" / "PHASE49_BOOT_GATEWAY_MENU.md"
MANIFEST = ROOT / "additive_content" / "gateway" / "phase49_boot_gateway_menu_manifest.json"
ORIGINAL_ENTRY = 0x080000C0
SCREEN_BYTES = 240 * 160 * 2

try:
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
except Exception as exc:  # pragma: no cover
    raise SystemExit("Missing keystone-engine. Install with: .venv/bin/python -m pip install keystone-engine") from exc

try:
    from PIL import Image, ImageDraw
except Exception as exc:  # pragma: no cover
    raise SystemExit("Missing Pillow. Install requirements.txt") from exc

FONT = {
    "A":["01110","10001","10001","11111","10001","10001","10001"],"B":["11110","10001","10001","11110","10001","10001","11110"],"C":["01111","10000","10000","10000","10000","10000","01111"],"D":["11110","10001","10001","10001","10001","10001","11110"],"E":["11111","10000","10000","11110","10000","10000","11111"],"F":["11111","10000","10000","11110","10000","10000","10000"],"G":["01111","10000","10000","10111","10001","10001","01111"],"H":["10001","10001","10001","11111","10001","10001","10001"],"I":["11111","00100","00100","00100","00100","00100","11111"],"J":["00001","00001","00001","00001","10001","10001","01110"],"K":["10001","10010","10100","11000","10100","10010","10001"],"L":["10000","10000","10000","10000","10000","10000","11111"],"M":["10001","11011","10101","10101","10001","10001","10001"],"N":["10001","11001","10101","10011","10001","10001","10001"],"O":["01110","10001","10001","10001","10001","10001","01110"],"P":["11110","10001","10001","11110","10000","10000","10000"],"Q":["01110","10001","10001","10001","10101","10010","01101"],"R":["11110","10001","10001","11110","10100","10010","10001"],"S":["01111","10000","10000","01110","00001","00001","11110"],"T":["11111","00100","00100","00100","00100","00100","00100"],"U":["10001","10001","10001","10001","10001","10001","01110"],"V":["10001","10001","10001","10001","01010","01010","00100"],"W":["10001","10001","10001","10101","10101","11011","10001"],"X":["10001","01010","01010","00100","01010","01010","10001"],"Y":["10001","01010","01010","00100","00100","00100","00100"],"Z":["11111","00001","00010","00100","01000","10000","11111"],
    "0":["01110","10001","10011","10101","11001","10001","01110"],"1":["00100","01100","00100","00100","00100","00100","01110"],"2":["01110","10001","00001","00010","00100","01000","11111"],"3":["11110","00001","00001","01110","00001","00001","11110"],"4":["00010","00110","01010","10010","11111","00010","00010"],"5":["11111","10000","10000","11110","00001","00001","11110"],"6":["01110","10000","10000","11110","10001","10001","01110"],"7":["11111","00001","00010","00100","01000","01000","01000"],"8":["01110","10001","10001","01110","10001","10001","01110"],"9":["01110","10001","10001","01111","00001","00001","01110"]," ":["00000","00000","00000","00000","00000","00000","00000"],"-":["00000","00000","00000","11111","00000","00000","00000"],":":["00000","00100","00100","00000","00100","00100","00000"],".":["00000","00000","00000","00000","00000","01100","01100"],"/":"00000 00001 00010 00100 01000 10000 00000".split(),"!":"00100 00100 00100 00100 00100 00000 00100".split(),
}

MENU_OPTIONS = [
    ("ORIGINAL", "BOOT BUUS FURY"),
    ("SUPER", "POST KID BUU GODS"),
    ("GT", "BLACK STAR BABY"),
    ("AF", "SSJ5 XICOR RIFT"),
    ("LOG1 DIM", "SAIYAN NAMEK MEMORY"),
    ("LOG2 DIM", "ANDROID CELL MEMORY"),
]
ROUTE_SCREENS = [
    ("SUPER ROUTE", "BEERUS  HIT  BLACK", "UI AND TOURNAMENT"),
    ("GT ROUTE", "BLACK STAR BALLS", "BABY  RILLDO  OMEGA"),
    ("AF ROUTE", "SSJ5  IKL  XICOR", "DIVINE FUSION"),
    ("LOG1 DIMENSION", "RADITZ  NAMEK", "FRIEZA MEMORY"),
    ("LOG2 DIMENSION", "ANDROID CELL ERA", "WEST CITY MEMORY"),
]


def draw_text(img: Image.Image, x: int, y: int, text: str, scale: int, color: tuple[int,int,int], shadow: tuple[int,int,int] | None = None) -> None:
    d = ImageDraw.Draw(img)
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        if shadow:
            for r, line in enumerate(glyph):
                for c, bit in enumerate(line):
                    if bit == "1":
                        d.rectangle((cx+c*scale+scale, y+r*scale+scale, cx+(c+1)*scale-1+scale, y+(r+1)*scale-1+scale), fill=shadow)
        for r, line in enumerate(glyph):
            for c, bit in enumerate(line):
                if bit == "1":
                    d.rectangle((cx+c*scale, y+r*scale, cx+(c+1)*scale-1, y+(r+1)*scale-1), fill=color)
        cx += 6 * scale


def centered(img: Image.Image, y: int, text: str, scale: int, color: tuple[int,int,int], shadow: tuple[int,int,int] | None = None) -> None:
    draw_text(img, max(0, (240 - len(text)*6*scale)//2), y, text, scale, color, shadow)


def make_bg() -> Image.Image:
    img = Image.new("RGB", (240, 160), (10, 12, 28))
    d = ImageDraw.Draw(img)
    for y in range(0, 160, 8):
        for x in range(0, 240, 8):
            s = ((x//8 + y//8) % 4) * 5
            d.rectangle((x, y, x+7, y+7), fill=(10+s, 12+s, 34+s))
            if (x*7 + y*3) % 97 == 0:
                d.point((x+4, y+4), fill=(200, 210, 255))
    d.ellipse((88, 28, 152, 92), outline=(118, 70, 220), width=2)
    d.ellipse((92, 32, 148, 88), outline=(255, 224, 92), width=1)
    return img


def make_menu(selected: int) -> Image.Image:
    img = make_bg()
    d = ImageDraw.Draw(img)
    centered(img, 8, "THE LEGACY", 2, (255, 236, 82), (72, 16, 16))
    centered(img, 27, "OF GOKU 4", 2, (255, 255, 255), (40, 62, 160))
    centered(img, 47, "GATEWAY TEST", 1, (126, 226, 255), (0, 0, 0))
    y = 62
    for idx, (label, sub) in enumerate(MENU_OPTIONS):
        fill = (28, 56, 68) if idx != selected else (86, 78, 22)
        outline = (90, 180, 220) if idx != selected else (255, 226, 80)
        d.rectangle((24, y-2, 216, y+14), fill=fill, outline=outline)
        if idx == selected:
            draw_text(img, 28, y+2, ">", 1, (255, 240, 90), (0,0,0))
        draw_text(img, 40, y+2, label, 1, (255,255,255), (0,0,0))
        draw_text(img, 110, y+2, sub[:17], 1, (180,220,250), (0,0,0))
        y += 16
    centered(img, 146, "UP/DOWN SELECT  A ENTER  START ORIGINAL", 1, (255, 232, 120), (0,0,0))
    return img


def make_route(title: str, line1: str, line2: str) -> Image.Image:
    img = make_bg()
    d = ImageDraw.Draw(img)
    d.rectangle((12, 20, 228, 132), fill=(12, 24, 44), outline=(255, 226, 80))
    centered(img, 36, title, 2, (255, 236, 82), (0,0,0))
    centered(img, 68, line1, 1, (126, 226, 255), (0,0,0))
    centered(img, 84, line2, 1, (255,255,255), (0,0,0))
    centered(img, 116, "B BACK   START BOOT ORIGINAL", 1, (255, 180, 100), (0,0,0))
    return img


def rgb555_bytes(img: Image.Image) -> bytes:
    img = img.convert("RGB")
    out = bytearray()
    for r, g, b in img.getdata():
        v = ((r >> 3) & 31) | (((g >> 3) & 31) << 5) | (((b >> 3) & 31) << 10)
        out.extend(struct.pack("<H", v))
    return bytes(out)


def build_images() -> bytes:
    images = [make_menu(i) for i in range(len(MENU_OPTIONS))]
    images += [make_route(*r) for r in ROUTE_SCREENS]
    preview_dir = ROOT / "additive_content" / "gateway_boot_menu"
    preview_dir.mkdir(parents=True, exist_ok=True)
    for i, img in enumerate(images):
        img.save(preview_dir / f"boot_gateway_screen_{i:02d}.png", optimize=True)
    return b"".join(rgb555_bytes(img) for img in images)

ASM = r"""
    .arm
_start:
    ldr sp, =0x03007F00
    ldr r0, =0x04000000
    ldr r1, =0x0403
    strh r1, [r0]
    mov r4, #0      @ selected menu index
    mov r5, #0      @ state: 0 menu, 1 route screen
    mov r0, #0
    bl copy_image
main_loop:
    bl wait_vblank
    bl read_keys
    cmp r0, #0
    beq main_loop
    cmp r5, #0
    bne route_input
menu_input:
    tst r0, #0x40   @ UP
    bne menu_up
    tst r0, #0x80   @ DOWN
    bne menu_down
    tst r0, #0x01   @ A
    bne menu_choose
    tst r0, #0x08   @ START
    bne jump_original
    b release_and_loop
menu_up:
    cmp r4, #0
    moveq r4, #5
    subne r4, r4, #1
    mov r0, r4
    bl copy_image
    b release_and_loop
menu_down:
    cmp r4, #5
    moveq r4, #0
    addne r4, r4, #1
    mov r0, r4
    bl copy_image
    b release_and_loop
menu_choose:
    cmp r4, #0
    beq jump_original
    mov r5, #1
    add r0, r4, #5  @ selected 1..5 -> route image 6..10
    bl copy_image
    b release_and_loop
route_input:
    tst r0, #0x02   @ B
    bne back_to_menu
    tst r0, #0x08   @ START
    bne jump_original
    b release_and_loop
back_to_menu:
    mov r5, #0
    mov r0, r4
    bl copy_image
release_and_loop:
    bl wait_release
    b main_loop

read_keys:
    ldr r1, =0x04000130
    ldrh r0, [r1]
    mvn r0, r0
    ldr r1, =0x03FF
    and r0, r0, r1
    bx lr

wait_release:
    stmdb sp!, {lr}
wr_loop:
    bl read_keys
    cmp r0, #0
    bne wr_loop
    ldmia sp!, {pc}

wait_vblank:
    ldr r0, =0x04000006
wv1:
    ldrh r1, [r0]
    cmp r1, #160
    blo wv1
wv2:
    ldrh r1, [r0]
    cmp r1, #160
    bhs wv2
    bx lr

copy_image:
    stmdb sp!, {r4-r8, lr}
    ldr r1, =IMAGE_BASE
    ldr r2, =76800
    mul r3, r0, r2
    add r1, r1, r3
    ldr r0, =0x06000000
    ldr r2, =38400
ci_loop:
    ldrh r3, [r1], #2
    strh r3, [r0], #2
    subs r2, r2, #1
    bne ci_loop
    ldmia sp!, {r4-r8, pc}

jump_original:
    ldr r0, =0x080000C0
    bx r0
"""


def assemble_code(appended_va: int, image_base: int) -> bytes:
    # Assemble twice: once with placeholder to learn length, then with final image base.
    def asm(img_base: int) -> bytes:
        text = ASM.replace("IMAGE_BASE", f"0x{img_base:08X}")
        ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
        enc, _ = ks.asm(text, addr=appended_va)
        return bytes(enc)
    first = asm(0xDEADBEEF)
    second = asm(appended_va + len(first))
    return second


def branch_opcode(src: int, dst: int) -> int:
    off = (dst - (src + 8)) // 4
    if not (-(1 << 23) <= off < (1 << 23)):
        raise ValueError("branch out of range")
    return 0xEA000000 | (off & 0x00FFFFFF)


def ips_patch(original: bytes, modified: bytes) -> bytes:
    out = bytearray(b"PATCH")
    pos = 0
    while pos < len(modified):
        if pos < len(original) and original[pos] == modified[pos]:
            pos += 1
            continue
        start = pos
        pos += 1
        while pos < len(modified) and pos - start < 0xFFFF:
            if pos < len(original) and original[pos] == modified[pos]:
                break
            pos += 1
        chunk = modified[start:pos]
        out.extend(start.to_bytes(3, "big"))
        out.extend(len(chunk).to_bytes(2, "big"))
        out.extend(chunk)
    out.extend(b"EOF")
    out.extend(len(modified).to_bytes(3, "big"))
    return bytes(out)


def hchk(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base ROM SHA-1 mismatch")
    images = build_images()
    appended_off = (len(base) + 3) & ~3
    appended_va = 0x08000000 + appended_off
    code = assemble_code(appended_va, appended_va)  # second pass computes base internally
    image_base = appended_va + len(code)
    # Reassemble with exact image base in case literal pool changed.
    code = assemble_code(appended_va, image_base)
    image_base = appended_va + len(code)
    modified = bytearray(base)
    modified.extend(b"\xFF" * (appended_off - len(modified)))
    modified.extend(code)
    modified.extend(images)
    struct.pack_into("<I", modified, 0, branch_opcode(0x08000000, appended_va))
    modified[0xA0:0xAC] = b"LOG4WARP49\0\0"
    modified[0xBD] = hchk(modified)
    while len(modified) % 4:
        modified.append(0)
    final = bytes(modified)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    manifest = {
        "schema": "jurai.phase49.boot_gateway_menu.v1",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "appended_code_va": f"0x{appended_va:08X}",
        "appended_code_size": len(code),
        "image_base_va": f"0x{image_base:08X}",
        "screen_count": 11,
        "controls": ["Up/Down select", "A/Start enter", "B back", "Start on route screen boots original"],
        "limitation": "route screens are debug warp information screens; actual map warps still require native map transition hook",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Phase 49 — Boot Gateway Menu\n\n"
        "Created a real boot-time Gateway selector hook before Buu's Fury starts.\n\n"
        f"Output ROM: `{gba.relative_to(ROOT)}`\n\n"
        f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n\n"
        "## Controls\n\n"
        "- Up/Down: select route.\n"
        "- A/Start on Original: boot Buu's Fury.\n"
        "- A/Start on Super/GT/AF/LOG1/LOG2: show route/dimension debug screen.\n"
        "- B: return to menu.\n"
        "- Start on route/dimension screen: boot Buu's Fury.\n\n"
        "This is the first true start-of-game warp selector. It is currently a route/debug screen selector; actual native map warps are the next hook.\n",
        encoding="utf-8",
    )
    txt.write_text(DOC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {gba}")
    print(f"Code size {len(code)} bytes, image base 0x{image_base:08X}, total {len(final)} bytes")


if __name__ == "__main__":
    main()
