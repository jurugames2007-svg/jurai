#!/usr/bin/env python3
"""Shared DLC asset pipeline for Phases 56-62.

The generated art in these phases is intentionally add-only: it creates GBA-sized
PNG payloads, manifests, a binary asset bank, and a ROM with the bank appended.
It does not replace base Buu's Fury assets or hook the new art into gameplay yet.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
PHASE54_SCRIPT = ROOT / "tools" / "phase54_register_native_map_stubs.py"
PHASE54_ROM = ROOT / "patch_output" / "DBZ_LOG4_phase54_gateway_native_map_registry.gba"

PH56 = ROOT / "additive_content" / "phase56_dlc_asset_audit"
PH57 = ROOT / "additive_content" / "phase57_playable_32x32_sprites"
PH58 = ROOT / "additive_content" / "phase58_ai_portraits"
PH59 = ROOT / "additive_content" / "phase59_enemy_32x32_sprites"
PH60 = ROOT / "additive_content" / "phase60_dlc_objects_tiles"
PH61 = ROOT / "additive_content" / "phase61_dlc_asset_bank"
PH62 = ROOT / "additive_content" / "phase62_dlc_readiness_pack"
DOCS = ROOT / "docs"
PATCH = ROOT / "patch_output"
INCLUDE = ROOT / "include"

PHASE61_PREFIX = PATCH / "DBZ_LOG4_phase61_dlc_asset_bank_payload"
PHASE62_ZIP = PATCH / "LOG4_v0_4_dlc_asset_readiness_pack.zip"
FIXED_ZIP_TIME = (2026, 8, 5, 12, 0, 0)

# 22 playable-route 32x32 sheets. IDs are content names used by the project docs;
# the graphics are original procedural GBA-style placeholders.
PLAYABLE_SPECS = [
    {"id": "goku_ssg", "route": "SUPER", "display": "Goku SSG", "primary": (230, 62, 42), "secondary": (42, 78, 160), "hair": (210, 34, 30), "aura": (255, 210, 80), "kind": "humanoid"},
    {"id": "goku_ssb", "route": "SUPER", "display": "Goku SSB", "primary": (48, 116, 224), "secondary": (230, 110, 34), "hair": (48, 202, 255), "aura": (96, 230, 255), "kind": "humanoid"},
    {"id": "goku_ui_sign", "route": "SUPER", "display": "Goku UI Sign", "primary": (50, 58, 76), "secondary": (232, 232, 232), "hair": (34, 38, 50), "aura": (210, 220, 255), "kind": "humanoid"},
    {"id": "goku_ui_mastered", "route": "SUPER", "display": "Goku UI Mastered", "primary": (236, 236, 240), "secondary": (58, 78, 120), "hair": (224, 224, 232), "aura": (255, 255, 255), "kind": "humanoid"},
    {"id": "vegeta_ssb", "route": "SUPER", "display": "Vegeta SSB", "primary": (28, 72, 178), "secondary": (236, 236, 244), "hair": (34, 198, 255), "aura": (92, 222, 255), "kind": "humanoid"},
    {"id": "vegeta_ssbe", "route": "SUPER", "display": "Vegeta SSBE", "primary": (18, 44, 162), "secondary": (255, 220, 70), "hair": (38, 132, 255), "aura": (90, 154, 255), "kind": "humanoid"},
    {"id": "vegeta_ultra_ego", "route": "SUPER", "display": "Vegeta Ultra Ego", "primary": (92, 34, 128), "secondary": (210, 190, 70), "hair": (180, 92, 230), "aura": (232, 92, 255), "kind": "humanoid"},
    {"id": "gohan_beast", "route": "SUPER", "display": "Gohan Beast", "primary": (92, 72, 118), "secondary": (250, 250, 250), "hair": (218, 220, 232), "aura": (245, 220, 255), "kind": "humanoid"},
    {"id": "trunks_rage", "route": "SUPER", "display": "Trunks Rage", "primary": (52, 60, 148), "secondary": (76, 220, 255), "hair": (184, 148, 238), "aura": (255, 242, 88), "kind": "sword"},
    {"id": "piccolo_orange", "route": "SUPER", "display": "Piccolo Orange", "primary": (230, 118, 46), "secondary": (65, 118, 64), "hair": (40, 120, 62), "aura": (255, 176, 70), "kind": "namek"},
    {"id": "android17_super", "route": "SUPER", "display": "Android 17", "primary": (34, 68, 74), "secondary": (220, 82, 62), "hair": (28, 32, 36), "aura": (72, 196, 220), "kind": "humanoid"},
    {"id": "android18_super", "route": "SUPER", "display": "Android 18", "primary": (72, 96, 168), "secondary": (232, 214, 76), "hair": (238, 218, 118), "aura": (164, 214, 255), "kind": "humanoid"},
    {"id": "gogeta_ssb", "route": "SUPER", "display": "Gogeta SSB", "primary": (38, 80, 190), "secondary": (238, 186, 58), "hair": (38, 190, 252), "aura": (110, 230, 255), "kind": "humanoid"},
    {"id": "vegito_blue", "route": "SUPER", "display": "Vegito Blue", "primary": (42, 70, 172), "secondary": (245, 128, 38), "hair": (48, 208, 255), "aura": (100, 226, 255), "kind": "humanoid"},
    {"id": "goku_ssj4", "route": "GT", "display": "Goku SSJ4", "primary": (178, 38, 48), "secondary": (64, 76, 112), "hair": (36, 30, 40), "aura": (255, 92, 64), "kind": "fur"},
    {"id": "vegeta_ssj4", "route": "GT", "display": "Vegeta SSJ4", "primary": (154, 42, 58), "secondary": (36, 54, 120), "hair": (84, 42, 64), "aura": (255, 112, 74), "kind": "fur"},
    {"id": "pan_gt", "route": "GT", "display": "Pan GT", "primary": (232, 82, 72), "secondary": (62, 82, 128), "hair": (30, 28, 32), "aura": (255, 160, 120), "kind": "humanoid"},
    {"id": "uub_majuub", "route": "GT", "display": "Majuub", "primary": (218, 190, 122), "secondary": (92, 52, 124), "hair": (38, 34, 42), "aura": (232, 226, 148), "kind": "humanoid"},
    {"id": "goku_ssj5_af", "route": "AF", "display": "Goku SSJ5", "primary": (238, 238, 232), "secondary": (156, 56, 64), "hair": (240, 240, 240), "aura": (255, 255, 255), "kind": "fur"},
    {"id": "vegeta_ssj5_af", "route": "AF", "display": "Vegeta SSJ5", "primary": (224, 224, 230), "secondary": (62, 68, 140), "hair": (236, 236, 242), "aura": (255, 245, 255), "kind": "fur"},
    {"id": "xicor_ally", "route": "AF", "display": "Xicor Ally", "primary": (218, 218, 228), "secondary": (112, 62, 154), "hair": (232, 232, 240), "aura": (212, 148, 255), "kind": "villain"},
    {"id": "kaioshin_af_ally", "route": "AF", "display": "AF Kaioshin", "primary": (92, 62, 144), "secondary": (232, 188, 72), "hair": (222, 230, 244), "aura": (184, 142, 255), "kind": "kai"},
]

ENEMY_SPECS = [
    {"id": "beerus_trial", "route": "SUPER", "display": "Beerus Trial", "primary": (94, 58, 138), "secondary": (236, 186, 64), "kind": "beast"},
    {"id": "frieza_soldier_super", "route": "SUPER", "display": "Frieza Soldier", "primary": (72, 112, 148), "secondary": (226, 226, 238), "kind": "soldier"},
    {"id": "golden_frieza", "route": "SUPER", "display": "Golden Frieza", "primary": (236, 190, 42), "secondary": (142, 48, 166), "kind": "alien"},
    {"id": "frost_memory", "route": "SUPER", "display": "Frost", "primary": (198, 206, 228), "secondary": (80, 94, 180), "kind": "alien"},
    {"id": "hit_trial", "route": "SUPER", "display": "Hit", "primary": (92, 54, 128), "secondary": (196, 100, 224), "kind": "assassin"},
    {"id": "goku_black_rift", "route": "SUPER", "display": "Black Rift", "primary": (42, 44, 54), "secondary": (232, 72, 138), "kind": "sword"},
    {"id": "zamasu_rift", "route": "SUPER", "display": "Zamasu", "primary": (78, 132, 82), "secondary": (224, 224, 238), "kind": "kai"},
    {"id": "fused_zamasu", "route": "SUPER", "display": "Fused Zamasu", "primary": (206, 216, 232), "secondary": (120, 74, 174), "kind": "boss"},
    {"id": "toppo_trial", "route": "SUPER", "display": "Toppo", "primary": (74, 58, 124), "secondary": (242, 202, 64), "kind": "heavy"},
    {"id": "jiren_trial", "route": "SUPER", "display": "Jiren", "primary": (188, 42, 42), "secondary": (42, 48, 54), "kind": "heavy"},
    {"id": "broly_vampa", "route": "SUPER", "display": "Broly", "primary": (76, 168, 72), "secondary": (90, 52, 112), "kind": "heavy"},
    {"id": "moro_scout", "route": "SUPER", "display": "Moro Scout", "primary": (64, 76, 92), "secondary": (156, 210, 236), "kind": "horned"},
    {"id": "moro_73", "route": "SUPER", "display": "Moro 73", "primary": (82, 92, 112), "secondary": (62, 192, 220), "kind": "horned"},
    {"id": "granolah_drone", "route": "SUPER", "display": "Granolah Drone", "primary": (72, 106, 84), "secondary": (228, 214, 84), "kind": "robot"},
    {"id": "baby_parasite", "route": "GT", "display": "Baby Parasite", "primary": (210, 210, 222), "secondary": (82, 134, 220), "kind": "crawler"},
    {"id": "baby_vegeta", "route": "GT", "display": "Baby Vegeta", "primary": (226, 220, 206), "secondary": (92, 118, 204), "kind": "villain"},
    {"id": "rilldo_machine", "route": "GT", "display": "Rilldo", "primary": (166, 62, 54), "secondary": (202, 202, 216), "kind": "robot"},
    {"id": "super17_core", "route": "GT", "display": "Super 17", "primary": (36, 36, 46), "secondary": (88, 172, 232), "kind": "android"},
    {"id": "hell_fighter_17", "route": "GT", "display": "Hell 17", "primary": (44, 54, 68), "secondary": (220, 92, 64), "kind": "android"},
    {"id": "nuova_shadow_dragon", "route": "GT", "display": "Nuova", "primary": (226, 98, 42), "secondary": (248, 214, 82), "kind": "dragon"},
    {"id": "eis_shadow_dragon", "route": "GT", "display": "Eis", "primary": (92, 174, 232), "secondary": (220, 242, 255), "kind": "dragon"},
    {"id": "omega_shadow_dragon", "route": "GT", "display": "Omega", "primary": (206, 222, 232), "secondary": (58, 76, 110), "kind": "dragon_boss"},
    {"id": "af_xicor_boss", "route": "AF", "display": "Xicor", "primary": (232, 232, 238), "secondary": (118, 66, 166), "kind": "boss"},
    {"id": "af_ikl_entity", "route": "AF", "display": "I'K'L", "primary": (44, 36, 64), "secondary": (214, 72, 180), "kind": "shadow"},
    {"id": "af_creator_drone", "route": "AF", "display": "Creator Drone", "primary": (88, 76, 118), "secondary": (238, 190, 82), "kind": "robot"},
    {"id": "af_frieza_revenge", "route": "AF", "display": "AF Frieza", "primary": (230, 232, 240), "secondary": (184, 72, 216), "kind": "alien"},
    {"id": "cell_jr_memory", "route": "LOG2", "display": "Cell Jr", "primary": (52, 184, 168), "secondary": (38, 82, 122), "kind": "alien"},
    {"id": "android19_memory", "route": "LOG2", "display": "Android 19", "primary": (226, 220, 210), "secondary": (238, 162, 72), "kind": "android"},
    {"id": "android20_memory", "route": "LOG2", "display": "Android 20", "primary": (92, 96, 110), "secondary": (232, 232, 232), "kind": "android"},
    {"id": "imperfect_cell_memory", "route": "LOG2", "display": "Imperfect Cell", "primary": (76, 166, 74), "secondary": (46, 70, 54), "kind": "bug"},
    {"id": "perfect_cell_memory", "route": "LOG2", "display": "Perfect Cell", "primary": (72, 188, 92), "secondary": (36, 62, 52), "kind": "bug"},
    {"id": "raditz_memory", "route": "LOG1", "display": "Raditz", "primary": (62, 54, 70), "secondary": (118, 84, 54), "kind": "saiyan"},
    {"id": "nappa_memory", "route": "LOG1", "display": "Nappa", "primary": (210, 172, 120), "secondary": (52, 58, 88), "kind": "heavy"},
    {"id": "saiyan_scout_memory", "route": "LOG1", "display": "Saiyan Scout", "primary": (88, 108, 78), "secondary": (206, 150, 70), "kind": "soldier"},
    {"id": "namek_frieza_soldier", "route": "LOG1", "display": "Namek Soldier", "primary": (80, 132, 160), "secondary": (226, 226, 236), "kind": "soldier"},
    {"id": "ginyu_memory", "route": "LOG1", "display": "Ginyu Memory", "primary": (88, 54, 130), "secondary": (220, 220, 232), "kind": "heavy"},
    {"id": "final_frieza_memory", "route": "LOG1", "display": "Final Frieza", "primary": (230, 232, 240), "secondary": (116, 72, 168), "kind": "alien"},
]

PORTRAIT_SPECS = [
    "hero_spiky", "stern_rival", "young_scholar", "time_warrior",
    "green_monk", "destroyer_mentor", "angel_mentor", "godki_fighter",
    "bio_alien", "warrior_monk", "cyborg_woman", "cyborg_ranger",
    "ancient_kai", "shadow_dragon", "lab_villain", "divine_boss",
]

OBJECT_SPECS = [
    ("senzu_bean", "Senzu", (90, 220, 80), "bean"),
    ("ultra_divine_water", "Divine Water", (92, 190, 255), "bottle"),
    ("beerus_ration", "Beerus Ration", (236, 196, 82), "food"),
    ("capsule_energy_drink", "Capsule Drink", (232, 64, 64), "capsule"),
    ("ki_battery", "Ki Battery", (84, 224, 255), "battery"),
    ("gravity_boots", "Gravity Boots", (118, 118, 134), "boots"),
    ("black_star_dragon_ball", "Black Star DB", (236, 118, 34), "ball"),
    ("time_chamber_key", "Time Key", (212, 222, 238), "key"),
    ("tournament_invitation", "Invitation", (238, 238, 190), "scroll"),
    ("moro_box", "Moro Box", (96, 70, 124), "box"),
    ("baby_scepter", "Baby Scepter", (216, 216, 230), "staff"),
    ("android17_core", "A17 Core", (80, 202, 232), "core"),
    ("negative_dragon_ball", "Negative DB", (72, 58, 98), "ball"),
    ("kaioshin_key", "Kai Key", (196, 152, 238), "key"),
    ("ikl_seal", "I'K'L Seal", (222, 64, 178), "seal"),
    ("stolen_goku_cells", "Stolen Cells", (80, 220, 142), "vial"),
    ("creator_heart", "Creator Heart", (238, 82, 128), "heart"),
    ("rift_shard_super", "Super Shard", (88, 222, 255), "crystal"),
    ("rift_shard_gt", "GT Shard", (255, 132, 72), "crystal"),
    ("rift_shard_af", "AF Shard", (216, 120, 255), "crystal"),
    ("log1_memory_chip", "LOG1 Chip", (100, 220, 100), "chip"),
    ("log2_memory_chip", "LOG2 Chip", (110, 220, 255), "chip"),
    ("gateway_capsule", "Gateway Cap", (242, 242, 242), "capsule"),
    ("debug_warp_pad", "Warp Pad", (255, 222, 70), "pad"),
    ("home_warp_pad", "Home Pad", (92, 220, 255), "pad"),
    ("origin_warp_pad", "Orig Pad", (255, 238, 92), "pad"),
    ("next_warp_pad", "Next Pad", (255, 148, 68), "pad"),
    ("dlc_route_token", "Route Token", (202, 182, 255), "token"),
]


def sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def hchk(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def rgb555(px: tuple[int, int, int, int] | tuple[int, int, int]) -> int:
    if len(px) == 4 and px[3] < 128:
        return 0
    r, g, b = px[:3]
    return ((r >> 3) & 31) | (((g >> 3) & 31) << 5) | (((b >> 3) & 31) << 10)


def image_to_rgb555_raw(path: Path) -> bytes:
    img = Image.open(path).convert("RGBA")
    out = bytearray()
    for px in img.getdata():
        out.extend(struct.pack("<H", rgb555(px)))
    return bytes(out)


def save_png(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def quantize_rgb(img: Image.Image, colors: int) -> Image.Image:
    # Keep alpha if present by quantizing RGB over a fixed transparent magenta matte.
    rgba = img.convert("RGBA")
    matte = Image.new("RGBA", rgba.size, (255, 0, 255, 0))
    matte.alpha_composite(rgba)
    rgb = Image.new("RGB", rgba.size, (255, 0, 255))
    rgb.paste(matte.convert("RGB"), mask=rgba.getchannel("A"))
    q = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    alpha = rgba.getchannel("A")
    q.putalpha(alpha)
    return q


def dark(c: tuple[int, int, int], amount: int = 50) -> tuple[int, int, int]:
    return tuple(max(0, v - amount) for v in c)


def light(c: tuple[int, int, int], amount: int = 48) -> tuple[int, int, int]:
    return tuple(min(255, v + amount) for v in c)


def draw_hair(d: ImageDraw.ImageDraw, x: int, y: int, hair: tuple[int, int, int], kind: str) -> None:
    outline = (22, 18, 24, 255)
    if kind in {"fur", "villain"}:
        pts = [(x + 16, y + 2), (x + 10, y + 8), (x + 12, y + 15), (x + 20, y + 15), (x + 22, y + 8)]
        d.polygon(pts, fill=hair + (255,), outline=outline)
        d.rectangle((x + 8, y + 10, x + 23, y + 14), fill=hair + (255,), outline=outline)
    elif kind == "namek":
        d.rectangle((x + 11, y + 8, x + 20, y + 10), fill=(52, 122, 58, 255), outline=outline)
        d.rectangle((x + 7, y + 10, x + 10, y + 13), fill=(52, 122, 58, 255), outline=outline)
        d.rectangle((x + 21, y + 10, x + 24, y + 13), fill=(52, 122, 58, 255), outline=outline)
    elif kind == "kai":
        d.rectangle((x + 10, y + 5, x + 21, y + 8), fill=hair + (255,), outline=outline)
        d.rectangle((x + 13, y + 2, x + 18, y + 6), fill=hair + (255,), outline=outline)
    else:
        pts = [(x + 16, y + 2), (x + 12, y + 8), (x + 7, y + 9), (x + 11, y + 12), (x + 9, y + 16), (x + 16, y + 13), (x + 23, y + 16), (x + 21, y + 11), (x + 25, y + 8), (x + 19, y + 8)]
        d.polygon(pts, fill=hair + (255,), outline=outline)


def draw_player_cell(spec: dict, frame: int) -> Image.Image:
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    p = tuple(spec["primary"])
    s = tuple(spec["secondary"])
    hair = tuple(spec["hair"])
    aura = tuple(spec["aura"])
    kind = str(spec["kind"])
    ox = [0, -1, 1][frame % 3]
    arm = 2 if frame == 2 else 0
    outline = (18, 18, 24, 255)
    skin = (226, 174, 118, 255) if kind not in {"namek", "kai"} else ((86, 154, 82, 255) if kind == "namek" else (226, 154, 210, 255))

    # Aura / silhouette, intentionally tile-ish and hard-edged.
    d.rectangle((8 + ox, 5, 23 + ox, 29), outline=aura + (190,))
    if frame == 2:
        d.rectangle((5 + ox, 10, 26 + ox, 28), outline=light(aura, 20) + (170,))

    # Legs.
    d.rectangle((11 + ox, 22, 14 + ox, 29), fill=dark(s, 18) + (255,), outline=outline)
    d.rectangle((18 + ox, 22, 21 + ox, 29), fill=dark(s, 18) + (255,), outline=outline)
    d.rectangle((9 + ox, 29, 15 + ox, 31), fill=dark(s, 45) + (255,))
    d.rectangle((17 + ox, 29, 23 + ox, 31), fill=dark(s, 45) + (255,))

    # Body and belt.
    d.rectangle((10 + ox, 14, 22 + ox, 23), fill=p + (255,), outline=outline)
    d.rectangle((11 + ox, 18, 21 + ox, 20), fill=s + (255,))
    d.rectangle((12 + ox, 15, 19 + ox, 16), fill=light(p, 38) + (255,))

    # Arms / weapon.
    d.rectangle((7 + ox - arm, 15, 10 + ox, 23), fill=p + (255,), outline=outline)
    d.rectangle((22 + ox, 15, 25 + ox + arm, 23), fill=p + (255,), outline=outline)
    if kind == "sword":
        d.rectangle((24 + ox + arm, 7, 26 + ox + arm, 22), fill=(210, 230, 250, 255), outline=outline)
    if kind == "fur":
        d.rectangle((8 + ox, 13, 23 + ox, 15), fill=(160, 42, 52, 255))

    # Head/face/hair.
    d.rectangle((12 + ox, 8, 20 + ox, 15), fill=skin, outline=outline)
    d.point((14 + ox, 11), fill=(20, 20, 28, 255))
    d.point((18 + ox, 11), fill=(20, 20, 28, 255))
    d.rectangle((15 + ox, 14, 18 + ox, 14), fill=(110, 52, 52, 255))
    draw_hair(d, ox, 0, hair, kind)
    return img


def draw_enemy_cell(spec: dict, frame: int) -> Image.Image:
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    p = tuple(spec["primary"])
    s = tuple(spec["secondary"])
    kind = str(spec["kind"])
    ox = [0, -1, 1][frame % 3]
    outline = (16, 16, 22, 255)

    if kind in {"dragon", "dragon_boss"}:
        d.rectangle((8 + ox, 13, 23 + ox, 24), fill=p + (255,), outline=outline)
        d.polygon([(12 + ox, 11), (16 + ox, 5), (20 + ox, 11)], fill=s + (255,), outline=outline)
        d.rectangle((10 + ox, 7, 22 + ox, 14), fill=p + (255,), outline=outline)
        d.rectangle((6 + ox, 16, 9 + ox, 19), fill=s + (255,), outline=outline)
        d.rectangle((23 + ox, 16, 26 + ox, 19), fill=s + (255,), outline=outline)
        d.line((22 + ox, 23, 29 + ox, 27), fill=s + (255,), width=2)
        if kind == "dragon_boss":
            d.rectangle((5 + ox, 8, 26 + ox, 25), outline=light(s, 30) + (255,))
    elif kind in {"robot", "android"}:
        d.rectangle((10 + ox, 8, 22 + ox, 17), fill=p + (255,), outline=outline)
        d.rectangle((12 + ox, 11, 20 + ox, 13), fill=s + (255,))
        d.rectangle((9 + ox, 17, 23 + ox, 26), fill=dark(p, 12) + (255,), outline=outline)
        d.rectangle((6 + ox, 18, 9 + ox, 24), fill=s + (255,), outline=outline)
        d.rectangle((23 + ox, 18, 26 + ox, 24), fill=s + (255,), outline=outline)
        d.rectangle((11 + ox, 26, 14 + ox, 31), fill=dark(p, 35) + (255,))
        d.rectangle((18 + ox, 26, 21 + ox, 31), fill=dark(p, 35) + (255,))
    elif kind in {"crawler", "bug"}:
        d.rectangle((8 + ox, 10, 23 + ox, 22), fill=p + (255,), outline=outline)
        d.rectangle((11 + ox, 7, 20 + ox, 13), fill=light(p, 28) + (255,), outline=outline)
        for y in (18, 22):
            d.line((8 + ox, y, 3 + ox, y + 3), fill=s + (255,), width=2)
            d.line((23 + ox, y, 28 + ox, y + 3), fill=s + (255,), width=2)
        d.rectangle((13 + ox, 11, 18 + ox, 13), fill=s + (255,))
    else:
        wide = kind in {"heavy", "boss", "horned"}
        x0, x1 = (8, 24) if wide else (10, 22)
        d.rectangle((x0 + ox, 14, x1 + ox, 25), fill=p + (255,), outline=outline)
        d.rectangle((x0 + 1 + ox, 18, x1 - 1 + ox, 20), fill=s + (255,))
        d.rectangle((11 + ox, 7, 21 + ox, 15), fill=light(p, 25) + (255,), outline=outline)
        d.point((14 + ox, 11), fill=(255, 48, 48, 255))
        d.point((18 + ox, 11), fill=(255, 48, 48, 255))
        if kind in {"horned", "boss", "beast"}:
            d.polygon([(11 + ox, 8), (7 + ox, 3), (13 + ox, 9)], fill=s + (255,), outline=outline)
            d.polygon([(21 + ox, 8), (25 + ox, 3), (19 + ox, 9)], fill=s + (255,), outline=outline)
        if kind in {"sword", "assassin"}:
            d.rectangle((23 + ox, 8, 25 + ox, 24), fill=light(s, 40) + (255,), outline=outline)
        d.rectangle((8 + ox, 25, 13 + ox, 31), fill=dark(p, 38) + (255,))
        d.rectangle((19 + ox, 25, 24 + ox, 31), fill=dark(p, 38) + (255,))
    if frame == 2:
        d.rectangle((5 + ox, 5, 27 + ox, 29), outline=s + (180,))
    return img


def make_sheet(spec: dict, enemy: bool) -> Image.Image:
    sheet = Image.new("RGBA", (96, 32), (0, 0, 0, 0))
    for frame in range(3):
        cell = draw_enemy_cell(spec, frame) if enemy else draw_player_cell(spec, frame)
        sheet.alpha_composite(cell, (frame * 32, 0))
    return quantize_rgb(sheet, 32)


def make_atlas(items: list[tuple[str, Path]], cell: int, title: str, columns: int = 10) -> Image.Image:
    rows = math.ceil(len(items) / columns)
    header = 14
    img = Image.new("RGBA", (columns * cell, rows * (cell + header)), (18, 20, 30, 255))
    d = ImageDraw.Draw(img)
    for idx, (label, path) in enumerate(items):
        x = (idx % columns) * cell
        y = (idx // columns) * (cell + header)
        tile = Image.open(path).convert("RGBA").resize((cell, cell), Image.Resampling.NEAREST)
        img.alpha_composite(tile, (x, y))
        d.rectangle((x, y, x + cell - 1, y + cell - 1), outline=(72, 150, 210, 255))
        d.text((x + 1, y + cell + 1), label[:6], fill=(238, 238, 150, 255))
    return img


def phase56() -> dict:
    PH56.mkdir(parents=True, exist_ok=True)
    audit = {
        "schema": "jurai.phase56.dlc_asset_audit.v1",
        "purpose": "Audit and generation target list for DLC-like 32x32 route assets.",
        "policy": "additive_asset_payloads_only_no_original_replacement",
        "target_cell_sizes": {"sprites": "32x32", "enemies": "32x32", "icons": "32x32", "portraits": "40x40 and 32x32 review thumbnails"},
        "playable_targets": PLAYABLE_SPECS,
        "enemy_targets": ENEMY_SPECS,
        "object_targets": [{"id": i, "display": d, "kind": k} for i, d, _c, k in OBJECT_SPECS],
        "portrait_targets": PORTRAIT_SPECS,
        "counts": {"playable": len(PLAYABLE_SPECS), "enemies": len(ENEMY_SPECS), "objects": len(OBJECT_SPECS), "portraits": len(PORTRAIT_SPECS)},
        "honest_status": "Generation targets. Downstream phases create draft/review-ready pixel assets; not yet hooked as animated engine OBJ records.",
    }
    (PH56 / "phase56_dlc_asset_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE56_DLC_ASSET_AUDIT.md").write_text(
        "# Phase 56 — DLC asset audit\n\n"
        "Created the add-only DLC asset target list for 32×32 sprites/enemies/icons and AI-assisted portraits.\n\n"
        f"- Playable sprite targets: {len(PLAYABLE_SPECS)}\n"
        f"- Enemy sprite targets: {len(ENEMY_SPECS)}\n"
        f"- Object/icon targets: {len(OBJECT_SPECS)}\n"
        f"- Portrait targets: {len(PORTRAIT_SPECS)}\n\n"
        "Status: planning/audit data only; generated art follows in Phases 57–60.\n",
        encoding="utf-8",
    )
    return audit


def phase57() -> dict:
    out_sheets = PH57 / "sheets_96x32"
    out_cells = PH57 / "cells_32x32"
    out_sheets.mkdir(parents=True, exist_ok=True)
    out_cells.mkdir(parents=True, exist_ok=True)
    records = []
    atlas_items = []
    for spec in PLAYABLE_SPECS:
        sheet = make_sheet(spec, enemy=False)
        sheet_path = out_sheets / f"{spec['id']}_sheet_3f_32x32.png"
        save_png(sheet, sheet_path)
        idle = sheet.crop((0, 0, 32, 32))
        cell_path = out_cells / f"{spec['id']}_idle_32x32.png"
        save_png(idle, cell_path)
        atlas_items.append((str(spec["id"]), cell_path))
        records.append({
            "id": spec["id"], "route": spec["route"], "display": spec["display"],
            "sheet": sheet_path.relative_to(ROOT).as_posix(), "idle_cell": cell_path.relative_to(ROOT).as_posix(),
            "cell_size": "32x32", "frames": 3, "palette_budget": 32,
        })
    atlas = make_atlas(atlas_items, 32, "phase57 playable", columns=8)
    atlas_path = PH57 / "phase57_playable_32x32_atlas.png"
    save_png(atlas, atlas_path)
    manifest = {"schema": "jurai.phase57.playable_32x32_sprites.v1", "records": records, "count": len(records), "atlas": atlas_path.relative_to(ROOT).as_posix(), "status": "draft_review_ready_not_hooked"}
    (PH57 / "phase57_playable_32x32_sprites_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE57_PLAYABLE_32X32_SPRITES.md").write_text(
        "# Phase 57 — Playable 32×32 sprite drafts\n\n"
        f"Generated {len(records)} original GBA-style 32×32 playable-route sprite sheets. Each sheet is 96×32 with 3 cells: idle, step, attack/charge.\n\n"
        f"Atlas: `{atlas_path.relative_to(ROOT)}`\n\n"
        "Status: draft/review-ready asset payloads; not yet inserted into engine OBJ animation tables.\n",
        encoding="utf-8",
    )
    return manifest


def crop_portraits_from_ai_source() -> list[dict]:
    source = PH58 / "ai_portrait_sheet_source.png"
    if not source.exists():
        raise SystemExit(f"Missing AI portrait source image: {source}")
    img = Image.open(source).convert("RGB")
    # Boxes tuned for the generated 4x4 source sheet. The resize/quantize step is
    # deterministic and produces native 40x40 portraits plus 32x32 thumbnails.
    boxes = []
    xs = [(314, 18, 493, 188), (516, 18, 696, 188), (718, 18, 898, 188), (918, 18, 1098, 188)]
    ys = [(18, 188), (208, 379), (398, 569), (588, 759)]
    for y0, y1 in ys:
        for x0, _dummy_y0, x1, _dummy_y1 in xs:
            boxes.append((x0, y0, x1, y1))
    p40_dir = PH58 / "portraits_40x40"
    p32_dir = PH58 / "portraits_32x32"
    p40_dir.mkdir(parents=True, exist_ok=True)
    p32_dir.mkdir(parents=True, exist_ok=True)
    records = []
    atlas_items = []
    for name, box in zip(PORTRAIT_SPECS, boxes):
        crop = img.crop(box)
        # Center-crop square before nearest-like pixel reduction.
        side = min(crop.width, crop.height)
        left = (crop.width - side) // 2
        top = (crop.height - side) // 2
        crop = crop.crop((left, top, left + side, top + side))
        p40 = quantize_rgb(crop.resize((40, 40), Image.Resampling.NEAREST), 32)
        p32 = quantize_rgb(crop.resize((32, 32), Image.Resampling.NEAREST), 32)
        path40 = p40_dir / f"{name}_portrait_40x40.png"
        path32 = p32_dir / f"{name}_portrait_32x32.png"
        save_png(p40, path40)
        save_png(p32, path32)
        atlas_items.append((name, path40))
        records.append({"id": name, "source_box": box, "portrait_40x40": path40.relative_to(ROOT).as_posix(), "portrait_32x32": path32.relative_to(ROOT).as_posix(), "palette_budget": 32})
    atlas = make_atlas(atlas_items, 40, "portraits", columns=8)
    atlas_path = PH58 / "phase58_ai_portrait_atlas_40x40.png"
    save_png(atlas, atlas_path)
    return records


def phase58() -> dict:
    PH58.mkdir(parents=True, exist_ok=True)
    records = crop_portraits_from_ai_source()
    source = PH58 / "ai_portrait_sheet_source.png"
    manifest = {
        "schema": "jurai.phase58.ai_portraits.v1",
        "source_image": source.relative_to(ROOT).as_posix(),
        "source_sha1": sha1(source),
        "records": records,
        "count": len(records),
        "atlas": (PH58 / "phase58_ai_portrait_atlas_40x40.png").relative_to(ROOT).as_posix(),
        "status": "AI-assisted portraits cropped/quantized for review; not final legal/title art; not hooked into dialogue UI yet.",
    }
    (PH58 / "phase58_ai_portraits_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE58_AI_PORTRAITS.md").write_text(
        "# Phase 58 — AI-assisted portraits\n\n"
        f"Processed the AI-assisted portrait sheet into {len(records)} native review portraits.\n\n"
        "Outputs:\n\n"
        f"- Source: `{source.relative_to(ROOT)}`\n"
        f"- 40×40 portraits: `{(PH58 / 'portraits_40x40').relative_to(ROOT)}`\n"
        f"- 32×32 thumbnails: `{(PH58 / 'portraits_32x32').relative_to(ROOT)}`\n"
        f"- Atlas: `{(PH58 / 'phase58_ai_portrait_atlas_40x40.png').relative_to(ROOT)}`\n\n"
        "Status: AI-assisted review assets, quantized toward GBA constraints; not yet wired to dialogue UI.\n",
        encoding="utf-8",
    )
    return manifest


def phase59() -> dict:
    out_sheets = PH59 / "sheets_96x32"
    out_cells = PH59 / "cells_32x32"
    out_sheets.mkdir(parents=True, exist_ok=True)
    out_cells.mkdir(parents=True, exist_ok=True)
    records = []
    atlas_items = []
    for spec in ENEMY_SPECS:
        sheet = make_sheet(spec, enemy=True)
        sheet_path = out_sheets / f"{spec['id']}_sheet_3f_32x32.png"
        save_png(sheet, sheet_path)
        idle = sheet.crop((0, 0, 32, 32))
        cell_path = out_cells / f"{spec['id']}_idle_32x32.png"
        save_png(idle, cell_path)
        atlas_items.append((str(spec["id"]), cell_path))
        records.append({
            "id": spec["id"], "route": spec["route"], "display": spec["display"], "kind": spec["kind"],
            "sheet": sheet_path.relative_to(ROOT).as_posix(), "idle_cell": cell_path.relative_to(ROOT).as_posix(),
            "cell_size": "32x32", "frames": 3, "palette_budget": 32,
        })
    atlas = make_atlas(atlas_items, 32, "phase59 enemies", columns=8)
    atlas_path = PH59 / "phase59_enemy_32x32_atlas.png"
    save_png(atlas, atlas_path)
    manifest = {"schema": "jurai.phase59.enemy_32x32_sprites.v1", "records": records, "count": len(records), "atlas": atlas_path.relative_to(ROOT).as_posix(), "status": "draft_review_ready_not_hooked"}
    (PH59 / "phase59_enemy_32x32_sprites_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE59_ENEMY_32X32_SPRITES.md").write_text(
        "# Phase 59 — Enemy 32×32 sprite drafts\n\n"
        f"Generated {len(records)} original GBA-style enemy/boss 32×32 sprite sheets. Each sheet is 96×32 with 3 cells.\n\n"
        f"Atlas: `{atlas_path.relative_to(ROOT)}`\n\n"
        "Status: draft/review-ready enemy asset payloads; not yet inserted into native enemy tables.\n",
        encoding="utf-8",
    )
    return manifest


def draw_icon(icon_id: str, label: str, color: tuple[int, int, int], kind: str) -> Image.Image:
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    outline = (18, 18, 24, 255)
    c = color
    d.rectangle((0, 0, 31, 31), fill=(16, 18, 28, 255), outline=(54, 88, 120, 255))
    if kind in {"ball", "core", "token"}:
        d.ellipse((8, 7, 24, 23), fill=c + (255,), outline=outline)
        d.ellipse((13, 11, 17, 15), fill=dark(c, 55) + (255,))
        if "dragon" in icon_id or "db" in icon_id:
            star = (32, 24, 40, 255) if "black" in icon_id or "negative" in icon_id else (226, 42, 28, 255)
            for x, y in [(13, 10), (17, 13), (14, 17)]:
                d.point((x, y), fill=star)
    elif kind in {"key"}:
        d.rectangle((8, 14, 24, 17), fill=c + (255,), outline=outline)
        d.ellipse((6, 11, 14, 19), outline=c + (255,), width=2)
        d.rectangle((22, 11, 24, 14), fill=c + (255,))
        d.rectangle((22, 18, 25, 20), fill=c + (255,))
    elif kind in {"crystal"}:
        d.polygon([(16, 5), (24, 13), (20, 26), (12, 26), (8, 13)], fill=c + (255,), outline=outline)
        d.line((16, 5, 16, 26), fill=light(c, 35) + (255,))
    elif kind in {"pad"}:
        d.rectangle((5, 11, 27, 24), fill=dark(c, 55) + (255,), outline=c + (255,))
        d.rectangle((8, 14, 24, 21), outline=light(c, 35) + (255,))
    elif kind in {"capsule"}:
        d.rounded_rectangle((8, 10, 24, 22), radius=5, fill=c + (255,), outline=outline)
        d.rectangle((15, 10, 17, 22), fill=(238, 238, 238, 255))
    elif kind in {"bottle", "vial"}:
        d.rectangle((13, 6, 19, 11), fill=(220, 230, 240, 255), outline=outline)
        d.rectangle((10, 11, 22, 25), fill=c + (255,), outline=outline)
        d.rectangle((12, 14, 20, 17), fill=light(c, 35) + (255,))
    elif kind in {"battery", "chip"}:
        d.rectangle((8, 9, 24, 24), fill=c + (255,), outline=outline)
        d.rectangle((12, 6, 20, 9), fill=light(c, 40) + (255,), outline=outline)
        for x in (11, 15, 19):
            d.line((x, 12, x, 21), fill=dark(c, 75) + (255,))
    elif kind == "heart":
        d.polygon([(16, 25), (7, 14), (10, 8), (16, 11), (22, 8), (25, 14)], fill=c + (255,), outline=outline)
        d.rectangle((14, 14, 18, 18), fill=light(c, 35) + (255,))
    elif kind == "staff":
        d.line((11, 25, 22, 7), fill=c + (255,), width=3)
        d.ellipse((18, 4, 27, 13), fill=light(c, 30) + (255,), outline=outline)
    elif kind == "boots":
        d.rectangle((8, 12, 14, 24), fill=c + (255,), outline=outline)
        d.rectangle((18, 12, 24, 24), fill=c + (255,), outline=outline)
        d.rectangle((7, 24, 15, 27), fill=dark(c, 40) + (255,))
        d.rectangle((17, 24, 25, 27), fill=dark(c, 40) + (255,))
    elif kind == "scroll":
        d.rectangle((8, 8, 24, 24), fill=c + (255,), outline=outline)
        d.line((10, 13, 22, 13), fill=dark(c, 80) + (255,))
        d.line((10, 17, 20, 17), fill=dark(c, 80) + (255,))
    elif kind == "box":
        d.rectangle((8, 10, 24, 25), fill=c + (255,), outline=outline)
        d.line((8, 15, 24, 15), fill=light(c, 35) + (255,))
    elif kind == "seal":
        d.ellipse((7, 7, 25, 25), fill=dark(c, 40) + (255,), outline=c + (255,))
        d.line((11, 16, 21, 16), fill=light(c, 40) + (255,), width=2)
        d.line((16, 11, 16, 21), fill=light(c, 40) + (255,), width=2)
    else:
        d.rectangle((10, 10, 22, 22), fill=c + (255,), outline=outline)
    # Small route/debug color tick.
    d.rectangle((2, 27, 29, 29), fill=dark(c, 28) + (255,))
    return quantize_rgb(img, 32)


def phase60() -> dict:
    icon_dir = PH60 / "icons_32x32"
    icon_dir.mkdir(parents=True, exist_ok=True)
    records = []
    atlas_items = []
    for icon_id, label, color, kind in OBJECT_SPECS:
        img = draw_icon(icon_id, label, color, kind)
        path = icon_dir / f"{icon_id}_32x32.png"
        save_png(img, path)
        atlas_items.append((icon_id, path))
        records.append({"id": icon_id, "display": label, "kind": kind, "icon": path.relative_to(ROOT).as_posix(), "cell_size": "32x32", "palette_budget": 32})
    atlas = make_atlas(atlas_items, 32, "phase60 objects", columns=8)
    atlas_path = PH60 / "phase60_object_icon_atlas.png"
    save_png(atlas, atlas_path)
    manifest = {"schema": "jurai.phase60.dlc_objects_tiles.v1", "records": records, "count": len(records), "atlas": atlas_path.relative_to(ROOT).as_posix(), "status": "object_icon_and_warp_tile_payloads_not_hooked"}
    (PH60 / "phase60_dlc_objects_tiles_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE60_DLC_OBJECTS_TILES.md").write_text(
        "# Phase 60 — DLC object icons and warp tiles\n\n"
        f"Generated {len(records)} 32×32 object/item/warp-pad icons for DLC route readiness.\n\n"
        f"Atlas: `{atlas_path.relative_to(ROOT)}`\n\n"
        "Status: add-only object/icon payloads; not yet inserted into item tables.\n",
        encoding="utf-8",
    )
    return manifest


def gather_bank_assets() -> list[dict]:
    assets: list[dict] = []
    for manifest_path, kind in [
        (PH57 / "phase57_playable_32x32_sprites_manifest.json", "playable_sprite_sheet"),
        (PH59 / "phase59_enemy_32x32_sprites_manifest.json", "enemy_sprite_sheet"),
        (PH58 / "phase58_ai_portraits_manifest.json", "portrait_40x40"),
        (PH60 / "phase60_dlc_objects_tiles_manifest.json", "object_icon_32x32"),
    ]:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rec in data["records"]:
            if kind == "portrait_40x40":
                path = ROOT / rec["portrait_40x40"]
                asset_id = rec["id"]
            elif kind == "object_icon_32x32":
                path = ROOT / rec["icon"]
                asset_id = rec["id"]
            else:
                path = ROOT / rec["sheet"]
                asset_id = rec["id"]
            img = Image.open(path).convert("RGBA")
            assets.append({
                "id": asset_id,
                "kind": kind,
                "path": path,
                "width": img.width,
                "height": img.height,
                "frames": 3 if img.width == 96 and img.height == 32 else 1,
            })
    return assets


def build_binary_bank(assets: list[dict]) -> tuple[bytes, dict]:
    raw_parts = []
    records = []
    offset = 0
    for idx, asset in enumerate(assets):
        raw = image_to_rgb555_raw(asset["path"])
        kind_id = {"playable_sprite_sheet": 1, "enemy_sprite_sheet": 2, "portrait_40x40": 3, "object_icon_32x32": 4}[asset["kind"]]
        records.append({
            "index": idx,
            "id": asset["id"],
            "kind": asset["kind"],
            "kind_id": kind_id,
            "width": asset["width"],
            "height": asset["height"],
            "frames": asset["frames"],
            "raw_offset": offset,
            "raw_size": len(raw),
            "source": asset["path"].relative_to(ROOT).as_posix(),
            "source_sha1": sha1(asset["path"]),
        })
        raw_parts.append(raw)
        offset += len(raw)
    bank_manifest = {"schema": "jurai.phase61.dlc_asset_bank.binary_manifest.v1", "asset_count": len(records), "records": records}
    manifest_bytes = json.dumps(bank_manifest, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    raw_blob = b"".join(raw_parts)
    header = b"LOG4A32\0" + struct.pack("<III", len(records), len(manifest_bytes), len(raw_blob))
    bank = header + manifest_bytes + raw_blob
    return bank, bank_manifest


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


def ensure_phase54() -> None:
    subprocess.run([sys.executable, str(PHASE54_SCRIPT)], cwd=ROOT, check=True)


def phase61() -> dict:
    ensure_phase54()
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base ROM SHA-1 mismatch")
    source = PHASE54_ROM.read_bytes()
    assets = gather_bank_assets()
    bank, bank_manifest = build_binary_bank(assets)
    out = bytearray(source)
    bank_off = (len(out) + 3) & ~3
    out.extend(b"\xFF" * (bank_off - len(out)))
    bank_va = 0x08000000 + bank_off
    out.extend(bank)
    out[0xA0:0xAC] = b"LOG4ASSET61\0"
    out[0xBD] = hchk(out)
    while len(out) % 4:
        out.append(0)
    final = bytes(out)
    gba = PHASE61_PREFIX.with_suffix(".gba")
    ips = PHASE61_PREFIX.with_suffix(".ips")
    txt = PHASE61_PREFIX.with_suffix(".txt")
    PATCH.mkdir(parents=True, exist_ok=True)
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    bank_path = PH61 / "log4_phase61_asset_bank.bin"
    PH61.mkdir(parents=True, exist_ok=True)
    bank_path.write_bytes(bank)
    bank_manifest_path = PH61 / "log4_phase61_asset_bank_manifest.json"
    bank_manifest_path.write_text(json.dumps(bank_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    INCLUDE.mkdir(parents=True, exist_ok=True)
    INCLUDE.joinpath("log4_phase61_asset_bank.h").write_text(
        "#pragma once\n"
        "// Auto-generated Phase 61 DLC asset bank location.\n"
        f"#define LOG4_PHASE61_ASSET_BANK_VA 0x{bank_va:08X}u\n"
        f"#define LOG4_PHASE61_ASSET_BANK_SIZE 0x{len(bank):X}u\n"
        f"#define LOG4_PHASE61_ASSET_COUNT {len(assets)}u\n",
        encoding="utf-8",
    )
    counts = {}
    for a in assets:
        counts[a["kind"]] = counts.get(a["kind"], 0) + 1
    manifest = {
        "schema": "jurai.phase61.dlc_asset_bank_payload.v1",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": sha1_bytes(final),
        "source_phase54_rom": PHASE54_ROM.relative_to(ROOT).as_posix(),
        "source_phase54_sha1": sha1(PHASE54_ROM),
        "asset_bank_bin": bank_path.relative_to(ROOT).as_posix(),
        "asset_bank_sha1": sha1_bytes(bank),
        "asset_bank_offset": f"0x{bank_off:06X}",
        "asset_bank_va": f"0x{bank_va:08X}",
        "asset_bank_size": len(bank),
        "asset_count": len(assets),
        "counts_by_kind": counts,
        "status": "ROM payload appended; assets are registered in a custom bank but not yet hooked into native renderer/entity tables.",
    }
    (PH61 / "phase61_dlc_asset_bank_payload_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    doc = (
        "# Phase 61 — DLC asset bank ROM payload\n\n"
        "Built a custom add-only `LOG4A32` binary bank from the Phase 57–60 assets and appended it to the Phase 54 native-registry ROM.\n\n"
        f"- Output ROM: `{gba.relative_to(ROOT)}`\n"
        f"- ROM SHA-1: `{sha1_bytes(final)}`\n"
        f"- Asset bank VA: `0x{bank_va:08X}`\n"
        f"- Asset bank size: `{len(bank)}` bytes\n"
        f"- Asset count: `{len(assets)}`\n"
        f"- Counts by kind: `{json.dumps(counts, sort_keys=True)}`\n\n"
        "Status: payload/bank only. The boot Gateway and original fallback remain playable, but the new art is not yet wired to native OBJ/entity tables.\n"
    )
    DOCS.joinpath("PHASE61_DLC_ASSET_BANK_PAYLOAD.md").write_text(doc, encoding="utf-8")
    txt.write_text(doc, encoding="utf-8")
    return manifest


def write_deterministic_zip(entries: list[tuple[Path, str]], zip_path: Path) -> None:
    tmp = zip_path.with_suffix(".zip.tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in sorted(entries, key=lambda x: x[1]):
            info = zipfile.ZipInfo(arc, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, src.read_bytes())
    if zip_path.exists():
        zip_path.unlink()
    tmp.rename(zip_path)


def phase62() -> dict:
    gba = PHASE61_PREFIX.with_suffix(".gba")
    ips = PHASE61_PREFIX.with_suffix(".ips")
    if not gba.exists():
        raise SystemExit("Run phase61 first")
    readiness = {
        "schema": "jurai.phase62.dlc_readiness_contract.v1",
        "release_goal": "Move from debug Gateway to DLC-like route content pipeline.",
        "playability": {
            "boot_gateway_rooms": "working from Phase 51/54/61",
            "original_fallback": "working",
            "native_map_registry": "registered F0:01..F0:05",
            "new_asset_bank": "appended LOG4A32 bank with 32x32 sprites/enemies/icons and portraits",
            "native_asset_render_hooks": "pending",
            "native_gateway_to_map_warp": "pending",
        },
        "route_asset_bindings": {
            "SUPER": [s["id"] for s in PLAYABLE_SPECS if s["route"] == "SUPER"] + [s["id"] for s in ENEMY_SPECS if s["route"] == "SUPER"],
            "GT": [s["id"] for s in PLAYABLE_SPECS if s["route"] == "GT"] + [s["id"] for s in ENEMY_SPECS if s["route"] == "GT"],
            "AF": [s["id"] for s in PLAYABLE_SPECS if s["route"] == "AF"] + [s["id"] for s in ENEMY_SPECS if s["route"] == "AF"],
            "LOG1_DIM": [s["id"] for s in ENEMY_SPECS if s["route"] == "LOG1"],
            "LOG2_DIM": [s["id"] for s in ENEMY_SPECS if s["route"] == "LOG2"],
        },
        "next_hooks": [
            "Gateway route selection -> native constructor around 0x08009030",
            "LOG4A32 bank reader -> native OBJ/Webfoot container converter",
            "Dialogue portrait pointer hook -> Phase 58 portrait bank",
            "Enemy spawn table hook -> Phase 59 enemy sheets",
            "Item table hook -> Phase 60 object icons",
        ],
    }
    PH62.mkdir(parents=True, exist_ok=True)
    readiness_path = PH62 / "phase62_dlc_readiness_contract.json"
    readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    readme = PATCH / "LOG4_v0_4_DLC_ASSET_READINESS_README.txt"
    readme.write_text(
        "Dragon Ball: The Legacy of Goku 4 — v0.4 DLC Asset Readiness\n"
        "============================================================\n\n"
        "Recommended advanced ROM:\n"
        "  roms/DBZ_LOG4_v0_4_DLCAssetBank.gba\n\n"
        f"ROM SHA-1: {sha1(gba)}\n"
        f"IPS SHA-1: {sha1(ips)}\n\n"
        "What this pack adds:\n"
        "- 22 playable-route 32x32 sprite sheets.\n"
        f"- {len(ENEMY_SPECS)} enemy/boss 32x32 sprite sheets.\n"
        f"- {len(OBJECT_SPECS)} object/item/warp 32x32 icons.\n"
        f"- {len(PORTRAIT_SPECS)} AI-assisted portraits in 40x40 and 32x32 review forms.\n"
        "- Appended LOG4A32 ROM asset bank.\n\n"
        "Honest limitation:\n"
        "- The Gateway rooms and original fallback are playable.\n"
        "- The new assets are payload/registry content and are not yet rendered by the native Buu's Fury engine.\n",
        encoding="utf-8",
    )
    docs = [
        DOCS / "PHASE56_DLC_ASSET_AUDIT.md",
        DOCS / "PHASE57_PLAYABLE_32X32_SPRITES.md",
        DOCS / "PHASE58_AI_PORTRAITS.md",
        DOCS / "PHASE59_ENEMY_32X32_SPRITES.md",
        DOCS / "PHASE60_DLC_OBJECTS_TILES.md",
        DOCS / "PHASE61_DLC_ASSET_BANK_PAYLOAD.md",
    ]
    DOCS.joinpath("PHASE62_DLC_READINESS_PACK.md").write_text(
        "# Phase 62 — v0.4 DLC asset readiness pack\n\n"
        "Packaged the seven-phase DLC asset-readiness block.\n\n"
        f"- Output package: `{PHASE62_ZIP.relative_to(ROOT)}`\n"
        f"- Recommended ROM inside package: `roms/DBZ_LOG4_v0_4_DLCAssetBank.gba`\n"
        f"- ROM SHA-1: `{sha1(gba)}`\n\n"
        "Status: playable Gateway rooms + original fallback remain available. New sprites/enemies/portraits/icons are packaged as an appended bank for the next renderer/entity hooks.\n",
        encoding="utf-8",
    )
    entries: list[tuple[Path, str]] = [
        (gba, "roms/DBZ_LOG4_v0_4_DLCAssetBank.gba"),
        (ips, "patches/DBZ_LOG4_v0_4_DLCAssetBank.ips"),
        (readme, "README.txt"),
        (readiness_path, "manifests/phase62_dlc_readiness_contract.json"),
        (PH61 / "phase61_dlc_asset_bank_payload_manifest.json", "manifests/phase61_dlc_asset_bank_payload_manifest.json"),
        (PH61 / "phase61_runtime_report.json", "manifests/phase61_runtime_report.json"),
        (PH61 / "log4_phase61_asset_bank_manifest.json", "manifests/log4_phase61_asset_bank_manifest.json"),
        (PH57 / "phase57_playable_32x32_sprites_manifest.json", "manifests/phase57_playable_32x32_sprites_manifest.json"),
        (PH58 / "phase58_ai_portraits_manifest.json", "manifests/phase58_ai_portraits_manifest.json"),
        (PH59 / "phase59_enemy_32x32_sprites_manifest.json", "manifests/phase59_enemy_32x32_sprites_manifest.json"),
        (PH60 / "phase60_dlc_objects_tiles_manifest.json", "manifests/phase60_dlc_objects_tiles_manifest.json"),
        (PH57 / "phase57_playable_32x32_atlas.png", "previews/phase57_playable_32x32_atlas.png"),
        (PH58 / "phase58_ai_portrait_atlas_40x40.png", "previews/phase58_ai_portrait_atlas_40x40.png"),
        (PH59 / "phase59_enemy_32x32_atlas.png", "previews/phase59_enemy_32x32_atlas.png"),
        (PH60 / "phase60_object_icon_atlas.png", "previews/phase60_object_icon_atlas.png"),
        (DOCS / "PHASE62_DLC_READINESS_PACK.md", "docs/PHASE62_DLC_READINESS_PACK.md"),
        (DOCS / "PHASE61_RUNTIME_DLC_ASSET_BANK.md", "docs/PHASE61_RUNTIME_DLC_ASSET_BANK.md"),
    ]
    runtime_evidence = [
        ROOT / "playtest_output" / "phase61_asset_bank_warp_rooms" / "phase51-warp-rooms-result.json",
        ROOT / "playtest_output" / "phase61_asset_bank_warp_rooms" / "screenshot-02_super_room_spawn.png",
        ROOT / "playtest_output" / "phase61_asset_bank_warp_rooms" / "screenshot-07_log2_after_next_pad.png",
        ROOT / "playtest_output" / "phase61_asset_bank_warp_rooms" / "screenshot-09_gateway_returned_from_home.png",
        ROOT / "playtest_output" / "phase61_asset_bank_original_fallback_skip" / "skip-playtest-result.json",
        ROOT / "playtest_output" / "phase61_asset_bank_original_fallback_skip" / "screenshot-final.png",
    ]
    for ev in runtime_evidence:
        if ev.exists():
            entries.append((ev, "runtime_evidence/" + ev.parent.name + "_" + ev.name))
    entries += [(d, "docs/" + d.name) for d in docs if d.exists()]
    write_deterministic_zip(entries, PHASE62_ZIP)
    manifest = {
        "schema": "jurai.release.v0_4_dlc_asset_readiness.v1",
        "package": PHASE62_ZIP.relative_to(ROOT).as_posix(),
        "package_sha1": sha1(PHASE62_ZIP),
        "recommended_rom_in_zip": "roms/DBZ_LOG4_v0_4_DLCAssetBank.gba",
        "rom_sha1": sha1(gba),
        "ips_sha1": sha1(ips),
        "source_phase": 61,
        "release_phase": 62,
        "phase_block": [56, 57, 58, 59, 60, 61, 62],
        "counts": {"playable_sheets": len(PLAYABLE_SPECS), "enemy_sheets": len(ENEMY_SPECS), "object_icons": len(OBJECT_SPECS), "portraits": len(PORTRAIT_SPECS)},
        "playable_gateway_rooms": True,
        "asset_bank_payload": True,
        "native_asset_hooks": False,
    }
    (PH62 / "phase62_dlc_readiness_pack_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def run_all() -> None:
    for fn in (phase56, phase57, phase58, phase59, phase60, phase61, phase62):
        result = fn()
        print(f"{result['schema']} OK")


if __name__ == "__main__":
    dispatch = sys.argv[1] if len(sys.argv) > 1 else "all"
    if dispatch == "56": phase56()
    elif dispatch == "57": phase57()
    elif dispatch == "58": phase58()
    elif dispatch == "59": phase59()
    elif dispatch == "60": phase60()
    elif dispatch == "61": phase61()
    elif dispatch == "62": phase62()
    elif dispatch == "all": run_all()
    else: raise SystemExit(f"Unknown phase dispatch: {dispatch}")
