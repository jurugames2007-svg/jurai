#!/usr/bin/env python3
"""Phases 63-72: DLC runtime hooks.

This block moves beyond asset payloads by applying runtime hooks to the boot
Gateway layer:

- Route rooms dynamically blit 32x32 playable sprites from the Phase 61 LOG4A32
  asset bank.
- Route rooms dynamically blit enemy sheets, portraits, and object icons from the
  same bank.
- The Gateway bridge scans Buu's Fury's native AreaEntry table for the registered F0:01..F0:05 route IDs, then stores the resolved native record pointer in EWRAM for test verification.

Honest scope: these are real runtime hooks, but still in the boot Gateway/debug
layer. They do not yet hand control to the Buu's Fury native map constructor.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM

# Reuse the existing hard-edged GBA font and patch helpers.
from phase51_boot_gateway_warp_rooms import FONT, draw_text, centered, rgb555_bytes, branch_opcode, ips_patch, hchk

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
PHASE61_SCRIPT = ROOT / "tools" / "phase61_dlc_asset_bank_payload.py"
PHASE61_ROM = ROOT / "patch_output" / "DBZ_LOG4_phase61_dlc_asset_bank_payload.gba"
PHASE61_MANIFEST = ROOT / "additive_content" / "phase61_dlc_asset_bank" / "phase61_dlc_asset_bank_payload_manifest.json"
BANK_MANIFEST = ROOT / "additive_content" / "phase61_dlc_asset_bank" / "log4_phase61_asset_bank_manifest.json"
BANK_BIN = ROOT / "additive_content" / "phase61_dlc_asset_bank" / "log4_phase61_asset_bank.bin"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase69_dlc_runtime_hooks"
PACK_ZIP = ROOT / "patch_output" / "LOG4_v0_5_dlc_runtime_hooks_pack.zip"
STATE_BASE = 0x0203F700
NATIVE_LOOKUP_THUMB = 0x080089FD
MAP_TABLE_LITERAL_REF = 0x00008A58
MAP_ENTRY_COUNT = 457
ORIGINAL_ENTRY = 0x080000C0
SCREEN_BYTES = 240 * 160 * 2
FIXED_ZIP_TIME = (2026, 8, 5, 12, 0, 0)

PHASE_DIRS = {
    63: ROOT / "additive_content" / "phase63_dlc_hook_bindings",
    64: ROOT / "additive_content" / "phase64_runtime_sprite_enemy_hook",
    65: ROOT / "additive_content" / "phase65_runtime_portrait_icon_hook",
    66: ROOT / "additive_content" / "phase66_native_lookup_bridge_hook",
    67: ROOT / "additive_content" / "phase67_route_state_ewram_hook",
    68: ROOT / "additive_content" / "phase68_dlc_room_ui_hook",
    69: ROOT / "additive_content" / "phase69_dlc_runtime_hooks_rom",
    70: ROOT / "additive_content" / "phase70_dlc_runtime_validation",
    71: ROOT / "additive_content" / "phase71_v05_dlc_runtime_hooks_pack",
    72: ROOT / "additive_content" / "phase72_hook_doctor",
}
DOCS = ROOT / "docs"

ROUTES = [
    {"index": 1, "key": "SUPER", "title": "SUPER HOOK", "subtitle": "F0:01 GOD KI DLC", "playable": "goku_ssb", "enemy": "golden_frieza", "portrait": "godki_fighter", "icon": "rift_shard_super", "accent": (82, 222, 255), "alt": (255, 226, 80), "base": (8, 16, 38), "floor": (22, 42, 76)},
    {"index": 2, "key": "GT", "title": "GT HOOK", "subtitle": "F0:02 BLACK STAR", "playable": "goku_ssj4", "enemy": "baby_vegeta", "portrait": "shadow_dragon", "icon": "black_star_dragon_ball", "accent": (255, 132, 72), "alt": (98, 230, 118), "base": (28, 12, 12), "floor": (70, 32, 24)},
    {"index": 3, "key": "AF", "title": "AF HOOK", "subtitle": "F0:03 SSJ5 XICOR", "playable": "goku_ssj5_af", "enemy": "af_xicor_boss", "portrait": "lab_villain", "icon": "rift_shard_af", "accent": (222, 196, 255), "alt": (255, 90, 190), "base": (22, 10, 40), "floor": (52, 26, 82)},
    {"index": 4, "key": "LOG1", "title": "LOG1 HOOK", "subtitle": "F0:04 SAIYAN NAMEK", "playable": "goku_ssg", "enemy": "final_frieza_memory", "portrait": "green_monk", "icon": "log1_memory_chip", "accent": (132, 236, 92), "alt": (82, 186, 255), "base": (10, 30, 18), "floor": (32, 76, 38)},
    {"index": 5, "key": "LOG2", "title": "LOG2 HOOK", "subtitle": "F0:05 ANDROID CELL", "playable": "trunks_rage", "enemy": "perfect_cell_memory", "portrait": "cyborg_woman", "icon": "log2_memory_chip", "accent": (118, 226, 255), "alt": (255, 214, 86), "base": (18, 24, 30), "floor": (54, 64, 70)},
]

MENU_OPTIONS = [
    ("ORIGINAL", "BOOT BUUS FURY"),
    ("SUPER", "DLC HOOK F0:01"),
    ("GT", "DLC HOOK F0:02"),
    ("AF", "DLC HOOK F0:03"),
    ("LOG1 DIM", "DLC HOOK F0:04"),
    ("LOG2 DIM", "DLC HOOK F0:05"),
]


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def current_map_table_va() -> int:
    return struct.unpack_from("<I", PHASE61_ROM.read_bytes(), MAP_TABLE_LITERAL_REF)[0]


def ensure_phase61() -> None:
    if not PHASE61_ROM.exists() or not PHASE61_MANIFEST.exists() or not BANK_MANIFEST.exists() or not BANK_BIN.exists():
        subprocess.run([sys.executable, str(PHASE61_SCRIPT)], cwd=ROOT, check=True)


def read_bank_records() -> tuple[int, int, dict[tuple[str, str], dict]]:
    phase61 = json.loads(PHASE61_MANIFEST.read_text(encoding="utf-8"))
    bank_va = int(str(phase61["asset_bank_va"]), 16)
    bank = BANK_BIN.read_bytes()
    if bank[:8] != b"LOG4A32\0":
        raise SystemExit("Invalid LOG4A32 bank header")
    count, manifest_len, raw_len = struct.unpack_from("<III", bank, 8)
    raw_base_va = bank_va + 20 + manifest_len
    bank_manifest = json.loads(BANK_MANIFEST.read_text(encoding="utf-8"))
    if count != bank_manifest["asset_count"]:
        raise SystemExit("LOG4A32 count mismatch")
    records: dict[tuple[str, str], dict] = {}
    for rec in bank_manifest["records"]:
        records[(rec["kind"], rec["id"])] = rec
    return bank_va, raw_base_va, records


def asset_src(raw_base_va: int, records: dict[tuple[str, str], dict], kind: str, asset_id: str) -> int:
    rec = records[(kind, asset_id)]
    return raw_base_va + int(rec["raw_offset"])


def route_bindings() -> tuple[dict, dict[str, int]]:
    bank_va, raw_base_va, records = read_bank_records()
    constants: dict[str, int] = {}
    bindings = []
    for route in ROUTES:
        key = route["key"]
        playable_src = asset_src(raw_base_va, records, "playable_sprite_sheet", str(route["playable"]))
        enemy_src = asset_src(raw_base_va, records, "enemy_sprite_sheet", str(route["enemy"]))
        portrait_src = asset_src(raw_base_va, records, "portrait_40x40", str(route["portrait"]))
        icon_src = asset_src(raw_base_va, records, "object_icon_32x32", str(route["icon"]))
        constants[f"PLAY_{key}"] = playable_src
        constants[f"ENEMY_{key}"] = enemy_src
        constants[f"PORTRAIT_{key}"] = portrait_src
        constants[f"ICON_{key}"] = icon_src
        bindings.append({
            "route": key,
            "route_index": route["index"],
            "native_pair": f"F0:{route['index']:02X}",
            "playable_asset": route["playable"],
            "enemy_asset": route["enemy"],
            "portrait_asset": route["portrait"],
            "icon_asset": route["icon"],
            "playable_src_va": f"0x{playable_src:08X}",
            "enemy_src_va": f"0x{enemy_src:08X}",
            "portrait_src_va": f"0x{portrait_src:08X}",
            "icon_src_va": f"0x{icon_src:08X}",
        })
    manifest = {
        "schema": "jurai.phase63.dlc_hook_bindings.v1",
        "asset_bank_va": f"0x{bank_va:08X}",
        "raw_base_va": f"0x{raw_base_va:08X}",
        "state_base": f"0x{STATE_BASE:08X}",
        "native_lookup_thumb_reference": f"0x{NATIVE_LOOKUP_THUMB:08X}",
        "native_map_table_va": f"0x{current_map_table_va():08X}",
        "map_entry_count": MAP_ENTRY_COUNT,
        "bindings": bindings,
        "status": "Raw LOG4A32 asset-bank addresses prepared for runtime blit hooks.",
    }
    return manifest, constants


def draw_room_bg(route: dict) -> Image.Image:
    base = route["base"]
    floor = route["floor"]
    accent = route["accent"]
    alt = route["alt"]
    img = Image.new("RGB", (240, 160), base)
    d = ImageDraw.Draw(img)
    for y in range(20, 160, 8):
        for x in range(0, 240, 8):
            checker = ((x // 8) + (y // 8) + int(route["index"])) % 3
            add = 0 if checker else 14
            f = tuple(min(255, int(v) + add) for v in floor)
            d.rectangle((x, y, x + 7, y + 7), fill=f)
            if checker == 1:
                d.line((x, y + 7, x + 7, y + 7), fill=tuple(max(0, int(v) - 14) for v in floor))
    d.rectangle((0, 0, 239, 19), fill=(6, 8, 18), outline=accent)
    draw_text(img, 6, 5, str(route["title"]), 1, accent, (0, 0, 0))
    draw_text(img, 94, 5, str(route["subtitle"])[:22], 1, (232, 240, 255), (0, 0, 0))

    # Dynamic asset target frames. ARM code blits into these boxes at runtime.
    def box(x0: int, y0: int, x1: int, y1: int, label: str, outline: tuple[int, int, int]) -> None:
        d.rectangle((x0, y0, x1, y1), fill=(12, 22, 34), outline=outline)
        d.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), outline=tuple(min(255, v + 40) for v in outline))
        draw_text(img, x0 + 2, max(20, y0 - 9), label, 1, (238, 238, 166), (0, 0, 0))

    box(34, 62, 67, 95, "HERO", accent)
    box(96, 28, 137, 69, "FACE", (255, 226, 80))
    box(144, 62, 177, 95, "ENEMY", alt)
    box(184, 76, 217, 109, "ITEM", (255, 226, 80))

    # Existing room controls/pads preserved from the prior playable layer.
    d.rectangle((10, 120, 58, 150), fill=(28, 50, 72), outline=accent)
    draw_text(img, 18, 130, "HOME", 1, (255, 255, 255), (0, 0, 0))
    d.rectangle((182, 120, 230, 150), fill=(72, 44, 28), outline=alt)
    draw_text(img, 190, 130, "NEXT", 1, (255, 255, 255), (0, 0, 0))
    d.rectangle((88, 82, 152, 108), fill=(58, 38, 78), outline=(255, 226, 80))
    draw_text(img, 106, 92, "ORIG", 1, (255, 255, 255), (0, 0, 0))
    centered(img, 112, f"NATIVE LOOKUP F0:{int(route['index']):02X}", 1, (180, 238, 255), (0, 0, 0))
    centered(img, 151, "DPAD MOVE  A PAD  B MENU  L/R ROOM", 1, (255, 236, 118), (0, 0, 0))
    return img


def make_menu(selected: int) -> Image.Image:
    img = Image.new("RGB", (240, 160), (10, 12, 28))
    d = ImageDraw.Draw(img)
    for y in range(0, 160, 8):
        for x in range(0, 240, 8):
            s = ((x // 8 + y // 8) % 4) * 5
            d.rectangle((x, y, x + 7, y + 7), fill=(10 + s, 12 + s, 34 + s))
    centered(img, 8, "THE LEGACY", 2, (255, 236, 82), (72, 16, 16))
    centered(img, 27, "OF GOKU 4", 2, (255, 255, 255), (40, 62, 160))
    centered(img, 47, "DLC HOOK TEST", 1, (126, 226, 255), (0, 0, 0))
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
    centered(img, 146, "A ENTER HOOK ROOM   START ORIGINAL", 1, (255, 232, 120), (0, 0, 0))
    return img


def build_images() -> bytes:
    images = [make_menu(i) for i in range(len(MENU_OPTIONS))]
    images += [draw_room_bg(route) for route in ROUTES]
    preview_dir = PHASE_DIRS[68]
    preview_dir.mkdir(parents=True, exist_ok=True)
    for i, img in enumerate(images):
        img.save(preview_dir / f"phase68_dlc_hook_screen_{i:02d}.png", optimize=True)
    return b"".join(rgb555_bytes(img) for img in images)

ASM_TEMPLATE = r"""
    .arm
_start:
    ldr sp, =0x03007F00
    ldr r0, =0x04000000
    ldr r1, =0x0403
    strh r1, [r0]
    mov r4, #0      @ selected menu/current route: 0 original, 1..5 DLC rooms
    mov r5, #0      @ state: 0 menu, 1 room
    mov r6, #120    @ player x
    mov r7, #110    @ player y
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
    tst r0, #0x40
    bne menu_up
    tst r0, #0x80
    bne menu_down
    tst r0, #0x01
    bne menu_choose
    tst r0, #0x08
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
    tst r0, #0x02
    bne back_to_menu
    tst r0, #0x08
    bne jump_original
    tst r0, #0x100
    bne next_room
    tst r0, #0x200
    bne prev_room
    tst r0, #0x01
    bne check_portal
    tst r0, #0x40
    bne room_up
    tst r0, #0x80
    bne room_down
    tst r0, #0x20
    bne room_left
    tst r0, #0x10
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
    cmp r7, #112
    bgt release_and_loop
    cmp r7, #78
    blt release_and_loop
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
    add r0, r4, #5
    bl copy_image
    bl native_lookup_route
    bl blit_route_assets
    bl draw_player
    ldmia sp!, {pc}

native_lookup_route:
    @ Direct native AreaEntry table bridge.  Phase 54 already extended the
    @ real table with F0:01..F0:05 records.  We scan that table from the
    @ Gateway hook and store the native record pointer in EWRAM.  This avoids
    @ ARM/Thumb interworking risk while still proving route IDs resolve in the
    @ native AreaEntry registry.
    stmdb sp!, {r4-r11, lr}
    ldr r6, =STATE_BASE
    ldr r7, =0x4B48344C    @ 'L4HK'
    str r7, [r6]
    str r4, [r6, #4]
    mov r0, #0xF0
    mov r1, r4
    orr r7, r1, r0, lsl #8
    str r7, [r6, #8]
    ldr r8, =MAP_TABLE_VA
    ldr r9, =MAP_ENTRY_COUNT
    mov r10, #0
    mov r11, #0
nlr_loop:
    cmp r10, r9
    bhs nlr_done
    ldrb r0, [r8]
    cmp r0, #0xF0
    bne nlr_next
    ldrb r0, [r8, #1]
    cmp r0, r4
    moveq r11, r8
    beq nlr_done
nlr_next:
    add r8, r8, #0x38
    add r10, r10, #1
    b nlr_loop
nlr_done:
    str r11, [r6, #12]
    ldmia sp!, {r4-r11, pc}

blit_route_assets:
    stmdb sp!, {lr}
    cmp r4, #1
    beq blit_super
    cmp r4, #2
    beq blit_gt
    cmp r4, #3
    beq blit_af
    cmp r4, #4
    beq blit_log1
    b blit_log2

blit_super:
    ldr r0, =PLAY_SUPER
    bl blit_playable
    ldr r0, =ENEMY_SUPER
    bl blit_enemy
    ldr r0, =PORTRAIT_SUPER
    bl blit_portrait
    ldr r0, =ICON_SUPER
    bl blit_icon
    b blit_done
blit_gt:
    ldr r0, =PLAY_GT
    bl blit_playable
    ldr r0, =ENEMY_GT
    bl blit_enemy
    ldr r0, =PORTRAIT_GT
    bl blit_portrait
    ldr r0, =ICON_GT
    bl blit_icon
    b blit_done
blit_af:
    ldr r0, =PLAY_AF
    bl blit_playable
    ldr r0, =ENEMY_AF
    bl blit_enemy
    ldr r0, =PORTRAIT_AF
    bl blit_portrait
    ldr r0, =ICON_AF
    bl blit_icon
    b blit_done
blit_log1:
    ldr r0, =PLAY_LOG1
    bl blit_playable
    ldr r0, =ENEMY_LOG1
    bl blit_enemy
    ldr r0, =PORTRAIT_LOG1
    bl blit_portrait
    ldr r0, =ICON_LOG1
    bl blit_icon
    b blit_done
blit_log2:
    ldr r0, =PLAY_LOG2
    bl blit_playable
    ldr r0, =ENEMY_LOG2
    bl blit_enemy
    ldr r0, =PORTRAIT_LOG2
    bl blit_portrait
    ldr r0, =ICON_LOG2
    bl blit_icon
blit_done:
    ldmia sp!, {pc}

blit_playable:
    stmdb sp!, {lr}
    mov r1, #96
    mov r2, #32
    mov r3, #32
    mov r8, #35
    mov r9, #63
    bl blit_asset_skip_zero
    ldmia sp!, {pc}
blit_enemy:
    stmdb sp!, {lr}
    mov r1, #96
    mov r2, #32
    mov r3, #32
    mov r8, #145
    mov r9, #63
    bl blit_asset_skip_zero
    ldmia sp!, {pc}
blit_portrait:
    stmdb sp!, {lr}
    mov r1, #40
    mov r2, #40
    mov r3, #40
    mov r8, #97
    mov r9, #29
    bl blit_asset_skip_zero
    ldmia sp!, {pc}
blit_icon:
    stmdb sp!, {lr}
    mov r1, #32
    mov r2, #32
    mov r3, #32
    mov r8, #185
    mov r9, #77
    bl blit_asset_skip_zero
    ldmia sp!, {pc}

blit_asset_skip_zero:
    stmdb sp!, {r4-r12, lr}
    mov r10, r0           @ source row pointer
    mov r11, r3           @ rows remaining
    ldr r12, =0x06000000
    mov r4, #240
    mul r5, r9, r4
    add r5, r5, r8
    lsl r5, r5, #1
    add r12, r12, r5      @ dest row pointer
    lsl r6, r1, #1        @ source row stride in bytes
    mov r7, #480          @ screen stride in bytes
basz_row:
    mov r0, r10
    mov r3, r12
    mov r5, r2
basz_col:
    ldrh r4, [r0], #2
    cmp r4, #0
    beq basz_skip
    strh r4, [r3]
basz_skip:
    add r3, r3, #2
    subs r5, r5, #1
    bne basz_col
    add r10, r10, r6
    add r12, r12, r7
    subs r11, r11, #1
    bne basz_row
    ldmia sp!, {r4-r12, pc}

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
    ldr r4, =0x03FF
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


def assemble_code(appended_va: int, image_base: int, constants: dict[str, int]) -> bytes:
    text = ASM_TEMPLATE
    replacements = {
        "STATE_BASE": f"0x{STATE_BASE:08X}",
        "NATIVE_LOOKUP_THUMB": f"0x{NATIVE_LOOKUP_THUMB:08X}",
        "MAP_TABLE_VA": f"0x{current_map_table_va():08X}",
        "MAP_ENTRY_COUNT": str(MAP_ENTRY_COUNT),
        "IMAGE_BASE": f"0x{image_base:08X}",
    }
    for k, v in constants.items():
        replacements[k] = f"0x{v:08X}"
    # Replace longer names first so PLAY_SUPER is not affected by a partial token.
    for k in sorted(replacements, key=len, reverse=True):
        text = text.replace(k, replacements[k])
    ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
    enc, _ = ks.asm(text, addr=appended_va)
    return bytes(enc)


def build_rom(constants: dict[str, int]) -> dict:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base ROM SHA-1 mismatch")
    source = bytearray(PHASE61_ROM.read_bytes())
    images = build_images()
    appended_off = (len(source) + 3) & ~3
    appended_va = 0x08000000 + appended_off
    provisional = assemble_code(appended_va, appended_va, constants)
    image_base = appended_va + len(provisional)
    code = assemble_code(appended_va, image_base, constants)
    image_base = appended_va + len(code)
    code = assemble_code(appended_va, image_base, constants)
    image_base = appended_va + len(code)
    source.extend(b"\xFF" * (appended_off - len(source)))
    source.extend(code)
    source.extend(images)
    struct.pack_into("<I", source, 0, branch_opcode(0x08000000, appended_va))
    source[0xA0:0xAC] = b"LOG4HOOK69\0\0"
    source[0xBD] = hchk(source)
    while len(source) % 4:
        source.append(0)
    final = bytes(source)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    doc = (
        "# Phase 69 — DLC runtime hooks ROM\n\n"
        "Built the runtime-hook ROM that keeps the boot Gateway playable while dynamically blitting DLC assets from the Phase 61 `LOG4A32` bank.\n\n"
        f"- Output ROM: `{gba.relative_to(ROOT)}`\n"
        f"- SHA-1: `{hashlib.sha1(final).hexdigest()}`\n"
        f"- Appended ARM hook VA: `0x{appended_va:08X}`\n"
        f"- Image base VA: `0x{image_base:08X}`\n"
        f"- EWRAM route-state base: `0x{STATE_BASE:08X}`\n\n"
        "Runtime hooks applied: sprite/enemy blit, portrait/icon blit, native AreaEntry table bridge, EWRAM route-state logging.\n\n"
        "Honest limitation: still a Gateway/debug-layer hook; native map constructor handoff remains pending.\n"
    )
    DOCS.joinpath("PHASE69_DLC_RUNTIME_HOOKS_ROM.md").write_text(doc, encoding="utf-8")
    txt.write_text(doc, encoding="utf-8")
    return {
        "schema": "jurai.phase69.dlc_runtime_hooks_rom.v1",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "source_phase61_rom": PHASE61_ROM.relative_to(ROOT).as_posix(),
        "source_phase61_sha1": sha1(PHASE61_ROM),
        "appended_code_va": f"0x{appended_va:08X}",
        "appended_code_size": len(code),
        "image_base_va": f"0x{image_base:08X}",
        "screen_count": len(images) // SCREEN_BYTES,
        "state_base": f"0x{STATE_BASE:08X}",
        "state_magic": "L4HK / 0x4B48344C",
        "hooks": ["runtime sprite blit", "runtime enemy blit", "runtime portrait blit", "runtime icon blit", "native AreaEntry table bridge", "EWRAM route-state hook"],
        "limitation": "Debug Gateway layer; no native map constructor handoff yet.",
    }


def write_phase_manifests(binding_manifest: dict, rom_manifest: dict) -> None:
    for d in PHASE_DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
    PHASE_DIRS[63].joinpath("phase63_dlc_hook_bindings.json").write_text(json.dumps(binding_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE63_DLC_HOOK_BINDINGS.md").write_text(
        "# Phase 63 — DLC hook bindings\n\n"
        "Resolved `LOG4A32` raw ROM addresses for route-specific playable, enemy, portrait, and icon assets.\n\n"
        f"Bindings: `{PHASE_DIRS[63].joinpath('phase63_dlc_hook_bindings.json').relative_to(ROOT)}`\n",
        encoding="utf-8",
    )
    p64 = {"schema": "jurai.phase64.runtime_sprite_enemy_hook.v1", "rom": rom_manifest["output_gba"], "sprite_enemy_hooks": [{"route": b["route"], "playable_src_va": b["playable_src_va"], "enemy_src_va": b["enemy_src_va"]} for b in binding_manifest["bindings"]], "status": "Applied in Phase 69 ROM via ARM blit_asset_skip_zero."}
    PHASE_DIRS[64].joinpath("phase64_runtime_sprite_enemy_hook_manifest.json").write_text(json.dumps(p64, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE64_RUNTIME_SPRITE_ENEMY_HOOK.md").write_text("# Phase 64 — Runtime sprite/enemy hook\n\nApplied dynamic 32×32 playable/enemy blits from the `LOG4A32` bank in the Phase 69 ROM.\n", encoding="utf-8")
    p65 = {"schema": "jurai.phase65.runtime_portrait_icon_hook.v1", "rom": rom_manifest["output_gba"], "portrait_icon_hooks": [{"route": b["route"], "portrait_src_va": b["portrait_src_va"], "icon_src_va": b["icon_src_va"]} for b in binding_manifest["bindings"]], "status": "Applied in Phase 69 ROM via ARM blit_asset_skip_zero."}
    PHASE_DIRS[65].joinpath("phase65_runtime_portrait_icon_hook_manifest.json").write_text(json.dumps(p65, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE65_RUNTIME_PORTRAIT_ICON_HOOK.md").write_text("# Phase 65 — Runtime portrait/icon hook\n\nApplied dynamic portrait and object/icon blits from the `LOG4A32` bank in the Phase 69 ROM.\n", encoding="utf-8")
    p66 = {"schema": "jurai.phase66.native_lookup_bridge_hook.v1", "rom": rom_manifest["output_gba"], "native_lookup_thumb_reference": f"0x{NATIVE_LOOKUP_THUMB:08X}", "bridge_kind": "direct native AreaEntry table scan", "registered_pairs": [b["native_pair"] for b in binding_manifest["bindings"]], "state_base": f"0x{STATE_BASE:08X}", "status": "Applied: Gateway room render scans the native AreaEntry table for F0 route IDs and stores pointer in EWRAM."}
    PHASE_DIRS[66].joinpath("phase66_native_lookup_bridge_hook_manifest.json").write_text(json.dumps(p66, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE66_NATIVE_LOOKUP_BRIDGE_HOOK.md").write_text("# Phase 66 — Native lookup bridge hook\n\nApplied a bridge from the ARM Gateway hook into Buu's Fury native AreaEntry table, scanning for route pairs `F0:01..F0:05`. The native Thumb lookup at `0x080089FC` remains documented as the reference implementation.\n", encoding="utf-8")
    p67 = {"schema": "jurai.phase67.route_state_ewram_hook.v1", "rom": rom_manifest["output_gba"], "state_base": f"0x{STATE_BASE:08X}", "layout": {"+0": "magic L4HK", "+4": "current route index", "+8": "native pair F0:route", "+12": "native AreaEntry pointer returned by lookup"}, "status": "Applied in Phase 69 ROM."}
    PHASE_DIRS[67].joinpath("phase67_route_state_ewram_hook_manifest.json").write_text(json.dumps(p67, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE67_ROUTE_STATE_EWRAM_HOOK.md").write_text("# Phase 67 — Route-state EWRAM hook\n\nApplied EWRAM route-state logging at `0x0203F700` for automated verification and future native handoff.\n", encoding="utf-8")
    p68 = {"schema": "jurai.phase68.dlc_room_ui_hook.v1", "rom": rom_manifest["output_gba"], "previews": [f"{PHASE_DIRS[68].relative_to(ROOT)}/phase68_dlc_hook_screen_{i:02d}.png" for i in range(11)], "status": "Applied: rooms expose dynamic asset boxes and native lookup labels."}
    PHASE_DIRS[68].joinpath("phase68_dlc_room_ui_hook_manifest.json").write_text(json.dumps(p68, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE68_DLC_ROOM_UI_HOOK.md").write_text("# Phase 68 — DLC room UI hook\n\nUpdated Gateway room backgrounds for dynamic asset slots: hero, face, enemy, item, plus native lookup route labels.\n", encoding="utf-8")
    PHASE_DIRS[69].joinpath("phase69_dlc_runtime_hooks_rom_manifest.json").write_text(json.dumps(rom_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_runtime_script() -> Path:
    script = ROOT / "tools" / "gba_headless" / "test_phase69_dlc_runtime_hooks.mjs"
    script.write_text("""import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';

const romPath = process.argv[2];
const out = process.argv[3] ?? 'playtest_output/phase69_dlc_runtime_hooks';
await fs.mkdir(out, { recursive: true });
const runtime = await HeadlessRuntime.create({ romPath, outputDir: out, logFn: () => {} });

const STATE = 0x0203F700;
const tap = async (button, times = 1) => {
  for (let i = 0; i < times; i++) {
    await press(button, { hold: 4 });
    await wait({ frames: 8 });
  }
};

const script = `
  const STATE = ${STATE};
  const tap = ${tap.toString()};
  await wait({frames:60});
  await takeScreenshot({name:'00_gateway_original'});
  await tap('down', 1);
  await tap('a', 1);
  await wait({frames:30});
  await takeScreenshot({name:'01_super_assets_hooked'});
  assert({memory:{address:STATE, equals:0x4c}});
  const magic = read32(STATE);
  const route = read32(STATE + 4);
  const pair = read32(STATE + 8);
  const ptr = read32(STATE + 12);
  console.log('state_super', magic.toString(16), route.toString(16), pair.toString(16), ptr.toString(16));
  if (magic !== 0x4B48344C || route !== 1 || pair !== 0xF001 || ptr === 0) throw new Error('SUPER state/native lookup failed');

  await tap('r', 1); await wait({frames:20}); await takeScreenshot({name:'02_gt_assets_hooked'});
  if (read32(STATE + 4) !== 2 || read32(STATE + 8) !== 0xF002 || read32(STATE + 12) === 0) throw new Error('GT state/native lookup failed');
  await tap('r', 1); await wait({frames:20}); await takeScreenshot({name:'03_af_assets_hooked'});
  if (read32(STATE + 4) !== 3 || read32(STATE + 8) !== 0xF003 || read32(STATE + 12) === 0) throw new Error('AF state/native lookup failed');
  await tap('r', 1); await wait({frames:20}); await takeScreenshot({name:'04_log1_assets_hooked'});
  if (read32(STATE + 4) !== 4 || read32(STATE + 8) !== 0xF004 || read32(STATE + 12) === 0) throw new Error('LOG1 state/native lookup failed');
  await tap('r', 1); await wait({frames:20}); await takeScreenshot({name:'05_log2_assets_hooked'});
  if (read32(STATE + 4) !== 5 || read32(STATE + 8) !== 0xF005 || read32(STATE + 12) === 0) throw new Error('LOG2 state/native lookup failed');
  await takeMemorySnapshot({name:'phase69-state-before-fallback', address: STATE, length: 32});

  await tap('b', 1); await wait({frames:20}); await takeScreenshot({name:'06_back_to_gateway'});
  await tap('a', 1); await wait({frames:20}); await takeScreenshot({name:'07_log2_reentered'});
  await tap('start', 1); await wait({frames:180}); await takeScreenshot({name:'08_original_fallback_after_start'});
  await takeMemorySnapshot({name:'phase69-state', address: STATE, length: 32});
`;
let status = 'PASS', error = null;
try {
  await runtime.executeScript(script);
  await runtime.writeFinalSaveState();
} catch (e) {
  status = 'FAIL';
  error = String(e.stack || e);
}
await fs.writeFile(`${out}/phase69-dlc-runtime-hooks-result.json`, JSON.stringify({ status, error }, null, 2));
if (status === 'FAIL') {
  console.error(error);
  process.exit(1);
}
console.log('PASS_PHASE69_DLC_RUNTIME_HOOKS');
""", encoding="utf-8")
    return script


def write_runtime_report(status: str = "NOT_RUN", error: str | None = None) -> dict:
    report = {
        "schema": "jurai.phase70.dlc_runtime_validation.v1",
        "rom": OUT_PREFIX.with_suffix(".gba").relative_to(ROOT).as_posix(),
        "rom_sha1": sha1(OUT_PREFIX.with_suffix(".gba")) if OUT_PREFIX.with_suffix(".gba").exists() else None,
        "runtime_status": status,
        "error": error,
        "output_dir": "playtest_output/phase69_dlc_runtime_hooks",
        "coverage": ["Gateway boots", "SUPER/GT/AF/LOG1/LOG2 dynamic asset blits", "native AreaEntry table bridge for F0:01..F0:05", "EWRAM route-state assertions", "original fallback"],
    }
    PHASE_DIRS[70].mkdir(parents=True, exist_ok=True)
    PHASE_DIRS[70].joinpath("phase70_dlc_runtime_validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE70_DLC_RUNTIME_VALIDATION.md").write_text(
        "# Phase 70 — DLC runtime validation\n\n"
        f"Status: `{status}`\n\n"
        "The runtime script validates dynamic asset blits, native lookup bridge state, and original fallback.\n",
        encoding="utf-8",
    )
    return report


def package_release(runtime_status: str = "NOT_RUN") -> dict:
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    readme = ROOT / "patch_output" / "LOG4_v0_5_DLC_RUNTIME_HOOKS_README.txt"
    readme.write_text(
        "Dragon Ball: The Legacy of Goku 4 — v0.5 DLC Runtime Hooks\n"
        "==========================================================\n\n"
        "Recommended test ROM:\n"
        "  roms/DBZ_LOG4_v0_5_DLCRuntimeHooks.gba\n\n"
        f"ROM SHA-1: {sha1(gba)}\n"
        f"IPS SHA-1: {sha1(ips)}\n\n"
        "What works now:\n"
        "- Boot Gateway rooms are playable.\n"
        "- Route rooms dynamically draw 32x32 playable/enemy sprites from the LOG4A32 bank.\n"
        "- Route rooms dynamically draw portraits/icons from the LOG4A32 bank.\n"
        "- Route room render scans the native AreaEntry table for F0:01..F0:05 and logs the pointer in EWRAM.\n"
        "- START/ORIG still boots original Buu's Fury.\n\n"
        "Honest limitation:\n"
        "- This still does not hand control to a native Buu's Fury map. It proves the runtime asset hooks and native lookup bridge before the constructor hook.\n",
        encoding="utf-8",
    )
    entries: list[tuple[Path, str]] = [
        (gba, "roms/DBZ_LOG4_v0_5_DLCRuntimeHooks.gba"),
        (ips, "patches/DBZ_LOG4_v0_5_DLCRuntimeHooks.ips"),
        (readme, "README.txt"),
    ]
    for phase, name in [
        (63, "phase63_dlc_hook_bindings.json"),
        (64, "phase64_runtime_sprite_enemy_hook_manifest.json"),
        (65, "phase65_runtime_portrait_icon_hook_manifest.json"),
        (66, "phase66_native_lookup_bridge_hook_manifest.json"),
        (67, "phase67_route_state_ewram_hook_manifest.json"),
        (68, "phase68_dlc_room_ui_hook_manifest.json"),
        (69, "phase69_dlc_runtime_hooks_rom_manifest.json"),
        (70, "phase70_dlc_runtime_validation_report.json"),
    ]:
        path = PHASE_DIRS[phase] / name
        if path.exists():
            entries.append((path, f"manifests/{name}"))
    for doc_name in [
        "PHASE63_DLC_HOOK_BINDINGS.md", "PHASE64_RUNTIME_SPRITE_ENEMY_HOOK.md", "PHASE65_RUNTIME_PORTRAIT_ICON_HOOK.md",
        "PHASE66_NATIVE_LOOKUP_BRIDGE_HOOK.md", "PHASE67_ROUTE_STATE_EWRAM_HOOK.md", "PHASE68_DLC_ROOM_UI_HOOK.md",
        "PHASE69_DLC_RUNTIME_HOOKS_ROM.md", "PHASE70_DLC_RUNTIME_VALIDATION.md",
        "PHASE71_V05_DLC_RUNTIME_HOOKS_PACK.md", "PHASE72_HOOK_DOCTOR.md",
    ]:
        p = DOCS / doc_name
        if p.exists():
            entries.append((p, f"docs/{doc_name}"))
    preview_dir = PHASE_DIRS[68]
    for p in sorted(preview_dir.glob("phase68_dlc_hook_screen_*.png")):
        entries.append((p, "previews/" + p.name))
    runtime_evidence = [
        ROOT / "playtest_output" / "phase69_dlc_runtime_hooks" / "phase69-dlc-runtime-hooks-result.json",
        ROOT / "playtest_output" / "phase69_dlc_runtime_hooks" / "memory-phase69-state-before-fallback.json",
        ROOT / "playtest_output" / "phase69_dlc_runtime_hooks" / "memory-phase69-state.json",
        ROOT / "playtest_output" / "phase69_dlc_runtime_hooks" / "screenshot-01_super_assets_hooked.png",
        ROOT / "playtest_output" / "phase69_dlc_runtime_hooks" / "screenshot-03_af_assets_hooked.png",
        ROOT / "playtest_output" / "phase69_dlc_runtime_hooks" / "screenshot-05_log2_assets_hooked.png",
        ROOT / "playtest_output" / "phase69_dlc_runtime_hooks" / "screenshot-08_original_fallback_after_start.png",
    ]
    for ev in runtime_evidence:
        if ev.exists():
            entries.append((ev, "runtime_evidence/" + ev.name))
    tmp = PACK_ZIP.with_suffix(".zip.tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in sorted(entries, key=lambda x: x[1]):
            info = zipfile.ZipInfo(arc, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, src.read_bytes())
    if PACK_ZIP.exists():
        PACK_ZIP.unlink()
    tmp.rename(PACK_ZIP)
    manifest = {
        "schema": "jurai.phase71.v05_dlc_runtime_hooks_pack.v1",
        "package": PACK_ZIP.relative_to(ROOT).as_posix(),
        "package_sha1": sha1(PACK_ZIP),
        "recommended_rom_in_zip": "roms/DBZ_LOG4_v0_5_DLCRuntimeHooks.gba",
        "rom_sha1": sha1(gba),
        "ips_sha1": sha1(ips),
        "runtime_status": runtime_status,
        "phase_block": list(range(63, 73)),
        "native_map_constructor_handoff": False,
        "runtime_asset_hooks": True,
        "native_areaentry_table_bridge": True,
        "original_fallback": True,
    }
    PHASE_DIRS[71].mkdir(parents=True, exist_ok=True)
    PHASE_DIRS[71].joinpath("phase71_v05_dlc_runtime_hooks_pack_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE71_V05_DLC_RUNTIME_HOOKS_PACK.md").write_text(
        "# Phase 71 — v0.5 DLC runtime hooks pack\n\n"
        f"Package: `{PACK_ZIP.relative_to(ROOT)}`\n\n"
        f"ROM SHA-1: `{sha1(gba)}`\n\n"
        f"Runtime status: `{runtime_status}`\n",
        encoding="utf-8",
    )
    return manifest


def write_phase72_note() -> None:
    PHASE_DIRS[72].mkdir(parents=True, exist_ok=True)
    note = {
        "schema": "jurai.phase72.hook_doctor.v1",
        "doctor_expected_update": "tools/project_doctor.py should include phase69 ROM and v0.5 package after this script runs.",
        "latest_rom": OUT_PREFIX.with_suffix(".gba").relative_to(ROOT).as_posix(),
        "latest_package": PACK_ZIP.relative_to(ROOT).as_posix(),
    }
    PHASE_DIRS[72].joinpath("phase72_hook_doctor_note.json").write_text(json.dumps(note, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE72_HOOK_DOCTOR.md").write_text("# Phase 72 — Hook doctor\n\nPrepared doctor/update metadata for the v0.5 DLC runtime hooks block.\n", encoding="utf-8")


def main() -> int:
    ensure_phase61()
    binding_manifest, constants = route_bindings()
    rom_manifest = build_rom(constants)
    write_phase_manifests(binding_manifest, rom_manifest)
    write_runtime_script()
    write_runtime_report("NOT_RUN")
    package_release("NOT_RUN")
    write_phase72_note()
    print(f"Wrote {OUT_PREFIX.with_suffix('.gba').relative_to(ROOT)}")
    print(f"ROM SHA-1 {sha1(OUT_PREFIX.with_suffix('.gba'))}")
    print(f"Wrote {PACK_ZIP.relative_to(ROOT)}")
    print(f"ZIP SHA-1 {sha1(PACK_ZIP)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
