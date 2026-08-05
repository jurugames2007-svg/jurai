#!/usr/bin/env python3
"""Phase 20: Gateway menu UI/data payload.

Creates a native-resolution 240x160 gateway menu preview, a tile-grid/layout
manifest, a UTF-16LE text bank, and an append-only ROM payload. This still does
not hook the gateway into runtime UI; it prepares the exact menu/data we will
wire after the post-Kid-Buu unlock/debug hook.
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
GATE = ROOT / "additive_content" / "gateway"
PLAY = ROOT / "additive_content" / "playability"
DOC = ROOT / "docs" / "PHASE20_GATEWAY_MENU_PAYLOAD.md"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase20_gateway_menu_payload"
MANIFEST = GATE / "phase20_gateway_menu_payload_manifest.json"
MAGIC = b"LOG4GW20"
VERSION = 1

OPTIONS = [
    {"id": "GATE_SUPER", "label": "SUPER", "subtitle": "Gods, universes, Goku Black", "target": "SUPER_ROUTE", "color": (45, 165, 235)},
    {"id": "GATE_GT", "label": "GT", "subtitle": "Black Star, Baby, Shadow Dragons", "target": "GT_ROUTE", "color": (218, 64, 56)},
    {"id": "GATE_AF", "label": "AF", "subtitle": "SSJ5, I'K'l, Xicor", "target": "AF_ROUTE", "color": (220, 220, 230)},
    {"id": "GATE_LOG1", "label": "LOG1 DIM", "subtitle": "Saiyan / Namek memory", "target": "LOG1_DIMENSION", "color": (238, 188, 72)},
    {"id": "GATE_LOG2", "label": "LOG2 DIM", "subtitle": "Android / Cell memory", "target": "LOG2_DIMENSION", "color": (98, 210, 128)},
]


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


def draw_menu() -> Path:
    GATE.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (240, 160), (18, 26, 46, 255))
    d = ImageDraw.Draw(img)
    # 8x8 tile-like background.
    for y in range(0, 160, 8):
        for x in range(0, 240, 8):
            shade = ((x // 8 + y // 8) % 3) * 6
            d.rectangle((x, y, x + 7, y + 7), fill=(18 + shade, 26 + shade, 46 + shade, 255))
            if (x + y) % 64 == 0:
                d.point((x + 4, y + 4), fill=(90, 140, 210, 255))
    d.rectangle((0, 0, 239, 21), fill=(22, 88, 64, 255))
    d.text((7, 5), "CAPSULE CORP RIFT GATE", fill=(248, 236, 132, 255))
    d.text((152, 5), "POST-KID BUU", fill=(200, 238, 255, 255))
    y = 28
    for idx, opt in enumerate(OPTIONS):
        color = opt["color"]
        box = (10, y, 229, y + 21)
        d.rectangle(box, outline=color + (255,), fill=(28, 38, 62, 255))
        d.rectangle((12, y + 2, 23, y + 13), fill=color + (255,))
        d.text((29, y + 3), opt["label"], fill=(255, 255, 255, 255))
        d.text((91, y + 3), opt["subtitle"][:28], fill=(190, 216, 236, 255))
        y += 24
    d.rectangle((0, 145, 239, 159), fill=(22, 88, 64, 255))
    d.text((6, 148), "A: ENTER  B: BACK  START: DEBUG", fill=(248, 236, 132, 255))
    preview = GATE / "gateway_menu_preview_240x160.png"
    img.convert("P", palette=Image.Palette.ADAPTIVE, colors=64).convert("RGBA").save(preview, optimize=True)
    return preview


def create_text_bank() -> Path:
    texts = ["CAPSULE CORP RIFT GATE", "POST-KID BUU", "A: ENTER", "B: BACK", "START: DEBUG"]
    for opt in OPTIONS:
        texts.extend([opt["label"], opt["subtitle"], opt["target"]])
    blob = bytearray()
    index = []
    for text in texts:
        offset = len(blob)
        blob.extend(text.encode("utf-16le"))
        blob.extend(b"\x00\x00")
        index.append({"text": text, "offset": offset, "bytes": len(text.encode("utf-16le")) + 2})
    path = GATE / "gateway_text_bank.utf16le.bin"
    path.write_bytes(bytes(blob))
    (GATE / "gateway_text_bank_index.json").write_text(json.dumps({"schema": "jurai.phase20.gateway_text_bank.v1", "strings": index}, indent=2) + "\n", encoding="utf-8")
    return path


def write_contracts(preview: Path, text_bank: Path) -> list[Path]:
    tilemap = {
        "schema": "jurai.phase20.gateway_menu_layout.v1",
        "screen": [240, 160],
        "tile": [8, 8],
        "grid": [30, 20],
        "preview": preview.relative_to(ROOT).as_posix(),
        "text_bank": text_bank.relative_to(ROOT).as_posix(),
        "options": OPTIONS,
        "native_ui_policy": "reuse Buu's Fury style: 240x160 screen, 8x8 tile grid, low-color hard-edge UI",
    }
    state = {
        "schema": "jurai.phase20.gateway_state_machine.v1",
        "locked_until_any_flag": ["STORY_KID_BUU_DEFEATED", "LOG4_DEBUG_GATEWAY_UNLOCKED"],
        "initial_state": "GATE_CLOSED",
        "states": {
            "GATE_CLOSED": {"on_unlock": "GATE_MENU"},
            "GATE_MENU": {"a": "ENTER_SELECTED", "b": "EXIT_GATE", "start": "DEBUG_ROUTE_SELECT"},
            "ENTER_SELECTED": {"sets_flag_template": "{target}_ENTERED", "loads_target": "selected.target"},
            "EXIT_GATE": {"returns_to": "Capsule Corp / Rift Lab"},
            "DEBUG_ROUTE_SELECT": {"requires": "LOG4_DEBUG_GATEWAY_UNLOCKED"},
        },
        "options": [{"id": opt["id"], "target": opt["target"]} for opt in OPTIONS],
    }
    paths = []
    for path, data in [(GATE / "gateway_menu_layout.json", tilemap), (GATE / "gateway_state_machine.json", state)]:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        paths.append(path)
    return [preview, text_bank, GATE / "gateway_text_bank_index.json", *paths]


def make_payload(paths: list[Path]) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in paths:
            zf.write(path, path.relative_to(ROOT).as_posix())
    return bio.getvalue()


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base SHA-1 mismatch")
    preview = draw_menu()
    text_bank = create_text_bank()
    files = write_contracts(preview, text_bank)
    payload = make_payload(files)
    directory = json.dumps({"schema": "jurai.phase20.gateway_menu_payload.v1", "files": [f.relative_to(ROOT).as_posix() for f in files], "payload_sha1": hashlib.sha1(payload).hexdigest()}, separators=(",", ":")).encode("utf-8")
    header = MAGIC + struct.pack("<III", VERSION, len(directory), len(payload))
    modified = bytearray(base + header + directory + payload)
    while len(modified) % 4:
        modified.append(0)
    modified_bytes = bytes(modified)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(modified_bytes)
    ips.write_bytes(ips_patch(base, modified_bytes))
    manifest = {
        "schema": "jurai.phase20.gateway_menu_build.v1",
        "policy": "append_only_gateway_menu_data_original_game_unchanged",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(modified_bytes).hexdigest(),
        "payload_offset": len(base) + len(header) + len(directory),
        "payload_size": len(payload),
        "files": [f.relative_to(ROOT).as_posix() for f in files],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Phase 20 — Gateway menu payload",
        "",
        "Created a 240x160 native-style gateway menu and state machine for post-Kid-Buu route/dimension selection.",
        "",
        f"Preview: `{preview.relative_to(ROOT)}`",
        f"Output ROM: `{gba.relative_to(ROOT)}`",
        f"Modified SHA-1: `{hashlib.sha1(modified_bytes).hexdigest()}`",
        "",
        "The menu is data-only until a later runtime UI hook displays it after Kid Buu or in debug mode.",
    ]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {preview}")
    print(f"Wrote {gba}")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
