#!/usr/bin/env python3
"""Phase 51: boot-time Gateway with playable warp rooms.

This extends the Phase 49 boot hook from static route screens into a self-contained
runtime debug hub.  The game still boots through appended ARM code before the
original Buu's Fury entry point, but each non-original route now opens a small
Mode 3 "dimension room" where the tester can move a marker and trigger warp
pads.

Important scope note: this is intentionally additive and self-contained.  It does
not overwrite Buu's Fury maps or saves, and it does not yet call the native map
transition function.  It gives us a safe playable warp-point test layer while the
true native map loader hook is researched.

Controls:
- Gateway menu: Up/Down selects, A enters a route room, Start boots original.
- In a route room: D-pad moves the marker.
- In a route room: A on HOME pad returns to menu.
- In a route room: A on NEXT pad warps to the next dimension room.
- In a route room: A on ORIG pad, or Start anywhere, boots original Buu's Fury.
- In a route room: L/R cycles previous/next route room.
- In a route room: B returns to the Gateway menu.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase51_boot_gateway_warp_rooms"
DOC = ROOT / "docs" / "PHASE51_BOOT_GATEWAY_WARP_ROOMS.md"
MANIFEST = ROOT / "additive_content" / "gateway_warp_rooms" / "phase51_boot_gateway_warp_rooms_manifest.json"
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
    "0":["01110","10001","10011","10101","11001","10001","01110"],"1":["00100","01100","00100","00100","00100","00100","01110"],"2":["01110","10001","00001","00010","00100","01000","11111"],"3":["11110","00001","00001","01110","00001","00001","11110"],"4":["00010","00110","01010","10010","11111","00010","00010"],"5":["11111","10000","10000","11110","00001","00001","11110"],"6":["01110","10000","10000","11110","10001","10001","01110"],"7":["11111","00001","00010","00100","01000","01000","01000"],"8":["01110","10001","10001","01110","10001","10001","01110"],"9":["01110","10001","10001","01111","00001","00001","01110"],
    " ":["00000","00000","00000","00000","00000","00000","00000"],"-":["00000","00000","00000","11111","00000","00000","00000"],":":["00000","00100","00100","00000","00100","00100","00000"],".":["00000","00000","00000","00000","00000","01100","01100"],"/":"00000 00001 00010 00100 01000 10000 00000".split(),"!":"00100 00100 00100 00100 00100 00000 00100".split(),">":"10000 01000 00100 00010 00100 01000 10000".split(),"<":"00001 00010 00100 01000 00100 00010 00001".split(),
}

MENU_OPTIONS = [
    ("ORIGINAL", "BOOT BUUS FURY"),
    ("SUPER", "POST KID BUU GODS"),
    ("GT", "BLACK STAR BABY"),
    ("AF", "SSJ5 XICOR RIFT"),
    ("LOG1 DIM", "SAIYAN NAMEK MEMORY"),
    ("LOG2 DIM", "ANDROID CELL MEMORY"),
]

ROOMS = [
    {
        "key": "SUPER",
        "title": "SUPER RIFT",
        "subtitle": "GODS KI / UI TEST ROOM",
        "base": (8, 16, 38),
        "floor": (22, 42, 76),
        "accent": (255, 220, 72),
        "alt": (72, 198, 255),
        "objects": ["BEERUS", "WHIS", "TOP"],
    },
    {
        "key": "GT",
        "title": "GT RIFT",
        "subtitle": "BLACK STAR / BABY ROOM",
        "base": (28, 12, 12),
        "floor": (70, 32, 24),
        "accent": (255, 118, 58),
        "alt": (108, 230, 118),
        "objects": ["PAN", "M2", "OMEGA"],
    },
    {
        "key": "AF",
        "title": "AF RIFT",
        "subtitle": "SSJ5 / XICOR ROOM",
        "base": (22, 10, 40),
        "floor": (52, 26, 82),
        "accent": (222, 196, 255),
        "alt": (255, 90, 190),
        "objects": ["SSJ5", "IKL", "XICOR"],
    },
    {
        "key": "LOG1",
        "title": "LOG1 DIM",
        "subtitle": "SAIYAN / NAMEK MEMORY",
        "base": (10, 30, 18),
        "floor": (32, 76, 38),
        "accent": (132, 236, 92),
        "alt": (82, 186, 255),
        "objects": ["RADITZ", "NAMEK", "FRIEZA"],
    },
    {
        "key": "LOG2",
        "title": "LOG2 DIM",
        "subtitle": "ANDROID / CELL MEMORY",
        "base": (18, 24, 30),
        "floor": (54, 64, 70),
        "accent": (118, 226, 255),
        "alt": (255, 214, 86),
        "objects": ["WEST", "17/18", "CELL"],
    },
]


def draw_text(img: Image.Image, x: int, y: int, text: str, scale: int, color: tuple[int, int, int], shadow: tuple[int, int, int] | None = None) -> None:
    d = ImageDraw.Draw(img)
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        if shadow:
            for r, line in enumerate(glyph):
                for c, bit in enumerate(line):
                    if bit == "1":
                        d.rectangle((cx + c * scale + scale, y + r * scale + scale, cx + (c + 1) * scale - 1 + scale, y + (r + 1) * scale - 1 + scale), fill=shadow)
        for r, line in enumerate(glyph):
            for c, bit in enumerate(line):
                if bit == "1":
                    d.rectangle((cx + c * scale, y + r * scale, cx + (c + 1) * scale - 1, y + (r + 1) * scale - 1), fill=color)
        cx += 6 * scale


def centered(img: Image.Image, y: int, text: str, scale: int, color: tuple[int, int, int], shadow: tuple[int, int, int] | None = None) -> None:
    draw_text(img, max(0, (240 - len(text) * 6 * scale) // 2), y, text, scale, color, shadow)


def make_bg() -> Image.Image:
    img = Image.new("RGB", (240, 160), (10, 12, 28))
    d = ImageDraw.Draw(img)
    for y in range(0, 160, 8):
        for x in range(0, 240, 8):
            s = ((x // 8 + y // 8) % 4) * 5
            d.rectangle((x, y, x + 7, y + 7), fill=(10 + s, 12 + s, 34 + s))
            if (x * 7 + y * 3) % 97 == 0:
                d.point((x + 4, y + 4), fill=(200, 210, 255))
    d.ellipse((88, 28, 152, 92), outline=(118, 70, 220), width=2)
    d.ellipse((92, 32, 148, 88), outline=(255, 224, 92), width=1)
    return img


def make_menu(selected: int) -> Image.Image:
    img = make_bg()
    d = ImageDraw.Draw(img)
    centered(img, 8, "THE LEGACY", 2, (255, 236, 82), (72, 16, 16))
    centered(img, 27, "OF GOKU 4", 2, (255, 255, 255), (40, 62, 160))
    centered(img, 47, "PLAYABLE WARP", 1, (126, 226, 255), (0, 0, 0))
    y = 62
    for idx, (label, sub) in enumerate(MENU_OPTIONS):
        fill = (28, 56, 68) if idx != selected else (86, 78, 22)
        outline = (90, 180, 220) if idx != selected else (255, 226, 80)
        d.rectangle((24, y - 2, 216, y + 14), fill=fill, outline=outline)
        if idx == selected:
            draw_text(img, 28, y + 2, ">", 1, (255, 240, 90), (0, 0, 0))
        draw_text(img, 40, y + 2, label, 1, (255, 255, 255), (0, 0, 0))
        draw_text(img, 110, y + 2, sub[:17], 1, (180, 220, 250), (0, 0, 0))
        y += 16
    centered(img, 146, "A ENTER ROOM   START ORIGINAL", 1, (255, 232, 120), (0, 0, 0))
    return img


def rect_label(img: Image.Image, box: tuple[int, int, int, int], label: str, fill: tuple[int, int, int], outline: tuple[int, int, int]) -> None:
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=fill, outline=outline)
    d.rectangle((x0 + 3, y0 + 3, x1 - 3, y1 - 3), outline=tuple(min(255, v + 50) for v in outline))
    draw_text(img, x0 + max(2, (x1 - x0 + 1 - len(label) * 6) // 2), y0 + 8, label, 1, (255, 255, 255), (0, 0, 0))


def make_room(room: dict[str, object], index: int) -> Image.Image:
    base = room["base"]  # type: ignore[index]
    floor = room["floor"]  # type: ignore[index]
    accent = room["accent"]  # type: ignore[index]
    alt = room["alt"]  # type: ignore[index]
    img = Image.new("RGB", (240, 160), base)  # type: ignore[arg-type]
    d = ImageDraw.Draw(img)

    # Hard-edged 8x8-tile floor, intentionally close to GBA tile-map readability.
    for y in range(20, 160, 8):
        for x in range(0, 240, 8):
            checker = ((x // 8) + (y // 8) + index) % 3
            add = 0 if checker else 14
            f = tuple(min(255, int(v) + add) for v in floor)  # type: ignore[arg-type]
            d.rectangle((x, y, x + 7, y + 7), fill=f)
            if checker == 1:
                d.line((x, y + 7, x + 7, y + 7), fill=tuple(max(0, int(v) - 14) for v in floor))  # type: ignore[arg-type]

    # Header and route identity.
    d.rectangle((0, 0, 239, 19), fill=(6, 8, 18), outline=accent)  # type: ignore[arg-type]
    draw_text(img, 8, 5, str(room["title"]), 1, accent, (0, 0, 0))  # type: ignore[arg-type]
    draw_text(img, 110, 5, str(room["subtitle"])[:20], 1, (232, 240, 255), (0, 0, 0))

    # Warp pads.  The ARM hook tests broad zones around these pads.
    rect_label(img, (10, 120, 58, 150), "HOME", (28, 50, 72), accent)  # type: ignore[arg-type]
    rect_label(img, (182, 120, 230, 150), "NEXT", (72, 44, 28), alt)  # type: ignore[arg-type]
    rect_label(img, (88, 28, 152, 54), "ORIG", (58, 38, 78), (255, 226, 80))

    # Portal lines / room structure.
    d.line((58, 135, 182, 135), fill=accent, width=2)  # type: ignore[arg-type]
    d.line((120, 54, 120, 135), fill=alt, width=1)  # type: ignore[arg-type]
    d.rectangle((70, 66, 170, 111), outline=accent, width=2)  # type: ignore[arg-type]
    d.rectangle((76, 72, 164, 105), outline=tuple(max(0, int(v) - 50) for v in accent), width=1)  # type: ignore[arg-type]

    # Route objects / encounter stubs.  These are labels now; they become native
    # NPC/enemy anchors when the map loader hook lands.
    objects = room["objects"]  # type: ignore[index]
    positions = [(26, 77), (96, 86), (174, 77)]
    for label, (x, y) in zip(objects, positions):  # type: ignore[arg-type]
        d.rectangle((x - 8, y - 8, x + 40, y + 12), fill=tuple(max(0, int(v) - 10) for v in floor), outline=alt)  # type: ignore[arg-type]
        draw_text(img, x - 4, y - 2, str(label)[:6], 1, (255, 255, 255), (0, 0, 0))

    centered(img, 151, "DPAD MOVE  A PAD  B MENU  L/R ROOM", 1, (255, 236, 118), (0, 0, 0))
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
    images += [make_room(room, i) for i, room in enumerate(ROOMS, start=1)]
    preview_dir = ROOT / "additive_content" / "gateway_warp_rooms"
    preview_dir.mkdir(parents=True, exist_ok=True)
    for i, img in enumerate(images):
        img.save(preview_dir / f"phase51_screen_{i:02d}.png", optimize=True)
    return b"".join(rgb555_bytes(img) for img in images)


ASM = r"""
    .arm
_start:
    ldr sp, =0x03007F00
    ldr r0, =0x04000000
    ldr r1, =0x0403
    strh r1, [r0]
    mov r4, #0      @ selected menu index/current route: 0 original, 1..5 dimensions
    mov r5, #0      @ state: 0 menu, 1 route room
    mov r6, #120    @ player x in route room
    mov r7, #110    @ player y in route room
    mov r0, #0
    bl copy_image
main_loop:
    bl wait_vblank
    bl read_keys
    cmp r0, #0
    beq main_loop
    cmp r5, #0
    bne room_input

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
    mov r6, #120
    mov r7, #110
    bl render_room
    b release_and_loop

room_input:
    tst r0, #0x02   @ B
    bne back_to_menu
    tst r0, #0x08   @ START
    bne jump_original
    tst r0, #0x100  @ R
    bne next_room
    tst r0, #0x200  @ L
    bne prev_room
    tst r0, #0x01   @ A
    bne check_portal
    tst r0, #0x40   @ UP
    bne room_up
    tst r0, #0x80   @ DOWN
    bne room_down
    tst r0, #0x20   @ LEFT
    bne room_left
    tst r0, #0x10   @ RIGHT
    bne room_right
    b release_and_loop

room_up:
    cmp r7, #28
    subhi r7, r7, #4
    bl render_room
    b release_and_loop
room_down:
    cmp r7, #146
    addlo r7, r7, #4
    bl render_room
    b release_and_loop
room_left:
    cmp r6, #14
    subhi r6, r6, #4
    bl render_room
    b release_and_loop
room_right:
    cmp r6, #226
    addlo r6, r6, #4
    bl render_room
    b release_and_loop

check_portal:
    cmp r7, #118
    blt check_orig_pad
    cmp r6, #64
    ble back_to_menu
    cmp r6, #176
    bge next_room
    b release_and_loop
check_orig_pad:
    cmp r7, #58
    bgt release_and_loop
    cmp r6, #84
    blt release_and_loop
    cmp r6, #156
    bgt release_and_loop
    b jump_original

next_room:
    cmp r4, #5
    moveq r4, #1
    addne r4, r4, #1
    mov r6, #120
    mov r7, #110
    bl render_room
    b release_and_loop
prev_room:
    cmp r4, #1
    moveq r4, #5
    subne r4, r4, #1
    mov r6, #120
    mov r7, #110
    bl render_room
    b release_and_loop
back_to_menu:
    mov r5, #0
    mov r0, r4
    bl copy_image
    b release_and_loop

release_and_loop:
    bl wait_release
    b main_loop

render_room:
    stmdb sp!, {lr}
    add r0, r4, #5  @ route 1..5 -> screen index 6..10
    bl copy_image
    bl draw_player
    ldmia sp!, {pc}

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

draw_player:
    stmdb sp!, {r4-r8, lr}
    sub r1, r7, #4
    mov r2, #240
    mul r3, r1, r2
    sub r0, r6, #4
    add r3, r3, r0
    lsl r3, r3, #1
    ldr r0, =0x06000000
    add r0, r0, r3
    ldr r4, =0x03FF       @ yellow outline
    mov r5, #9
dp_row_loop:
    mov r8, r0
    mov r2, #9
dp_col_loop:
    strh r4, [r8], #2
    subs r2, r2, #1
    bne dp_col_loop
    add r0, r0, #480
    subs r5, r5, #1
    bne dp_row_loop
    @ white 3x3 core
    sub r1, r7, #1
    mov r2, #240
    mul r3, r1, r2
    sub r0, r6, #1
    add r3, r3, r0
    lsl r3, r3, #1
    ldr r0, =0x06000000
    add r0, r0, r3
    ldr r4, =0x7FFF
    mov r5, #3
dp_core_row:
    mov r8, r0
    mov r2, #3
dp_core_col:
    strh r4, [r8], #2
    subs r2, r2, #1
    bne dp_core_col
    add r0, r0, #480
    subs r5, r5, #1
    bne dp_core_row
    ldmia sp!, {r4-r8, pc}

jump_original:
    ldr r0, =0x080000C0
    bx r0
"""


def assemble_code(appended_va: int, image_base: int) -> bytes:
    text = ASM.replace("IMAGE_BASE", f"0x{image_base:08X}")
    ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
    enc, _ = ks.asm(text, addr=appended_va)
    return bytes(enc)


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
    provisional = assemble_code(appended_va, appended_va)
    image_base = appended_va + len(provisional)
    code = assemble_code(appended_va, image_base)
    image_base = appended_va + len(code)
    # Re-assemble once more in case the literal pool changed length due to the exact image base.
    code = assemble_code(appended_va, image_base)
    image_base = appended_va + len(code)

    modified = bytearray(base)
    modified.extend(b"\xFF" * (appended_off - len(modified)))
    modified.extend(code)
    modified.extend(images)
    struct.pack_into("<I", modified, 0, branch_opcode(0x08000000, appended_va))
    modified[0xA0:0xAC] = b"LOG4WARP51\0\0"
    modified[0xBD] = hchk(modified)
    while len(modified) % 4:
        modified.append(0)
    final = bytes(modified)

    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    OUT_PREFIX.parent.mkdir(parents=True, exist_ok=True)
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))

    manifest = {
        "schema": "jurai.phase51.boot_gateway_warp_rooms.v1",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "base_sha1": BASE_SHA1,
        "appended_code_va": f"0x{appended_va:08X}",
        "appended_code_size": len(code),
        "image_base_va": f"0x{image_base:08X}",
        "screen_count": len(images) // SCREEN_BYTES,
        "screen_bytes_each": SCREEN_BYTES,
        "title": "LOG4WARP51",
        "route_rooms": [room["key"] for room in ROOMS],
        "controls": [
            "Menu Up/Down select",
            "Menu A enters route room; Menu Start boots original",
            "Room D-pad moves marker",
            "Room A on HOME pad returns to menu",
            "Room A on NEXT pad warps to next route room",
            "Room A on ORIG pad or Start boots original Buu's Fury",
            "Room L/R cycles previous/next route room",
            "Room B returns to menu",
        ],
        "playability_status": "Playable self-contained warp-room layer from boot. Native Buu's Fury map transition is still pending.",
        "safety": "Additive appended ROM hook; original entry point remains available and original map/save data are not modified.",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = (
        "# Phase 51 — Boot Gateway Playable Warp Rooms\n\n"
        "Phase 51 upgrades the Phase 49 boot Gateway from static route info screens into a playable, self-contained warp-point layer.\n\n"
        f"- Output ROM: `{gba.relative_to(ROOT)}`\n"
        f"- IPS patch: `{ips.relative_to(ROOT)}`\n"
        f"- Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n"
        f"- Header title: `LOG4WARP51`\n"
        f"- Appended ARM code VA: `0x{appended_va:08X}`\n"
        f"- Image base VA: `0x{image_base:08X}`\n\n"
        "## What is playable now\n\n"
        "- Start the ROM and the Gateway selector appears immediately.\n"
        "- Choose `SUPER`, `GT`, `AF`, `LOG1 DIM`, or `LOG2 DIM` with A.\n"
        "- Each route opens a route-specific 240x160 GBA Mode 3 room.\n"
        "- D-pad moves the yellow/white tester marker.\n"
        "- A on `HOME` returns to the Gateway menu.\n"
        "- A on `NEXT` warps to the next dimension room.\n"
        "- A on `ORIG`, or Start anywhere in a room, boots the untouched original Buu's Fury entry point.\n"
        "- L/R cycles previous/next dimension room for fast testing.\n"
        "- B returns to the Gateway menu.\n\n"
        "## Honest limitation\n\n"
        "This is a real runtime/playable hook, but it is still a debug warp-room layer drawn by our appended ARM code. It does **not yet** invoke the native Buu's Fury map loader or place the player on original engine maps. That is the next engineering target.\n\n"
        "## Safety\n\n"
        "The build remains additive: it appends code and screen data after the base ROM, branches at boot, and preserves `Start`/`ORIG` as a fallback into the original `0x080000C0` Buu's Fury entry. No original maps, flags, or save structures are overwritten by this phase.\n"
    )
    DOC.write_text(doc, encoding="utf-8")
    txt.write_text(doc, encoding="utf-8")

    print(f"Wrote {gba.relative_to(ROOT)}")
    print(f"SHA-1 {hashlib.sha1(final).hexdigest()}")
    print(f"Code size {len(code)} bytes, image base 0x{image_base:08X}, total {len(final)} bytes")


if __name__ == "__main__":
    main()
