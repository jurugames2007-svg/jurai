#!/usr/bin/env python3
"""Phase 25 (Route A): Snakeway NPC visual-confirmation variant matrix.

Generates several experimental ROMs that all keep the original ROM bytes intact
and only redirect the known map-entry table literal to an appended extended
map-entry table. Each variant points Snakeway/Riftway to a different native
0x20-byte NPC record template/field mutation so we can manually discover which
field controls visible actor/sprite/interactability.

This is Route A: visual confirmation by variants.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
OUT_DIR = ROOT / "patch_output" / "phase25_snakeway_variants"
MANIFEST = ROOT / "additive_content" / "gateway" / "phase25_snakeway_npc_variant_matrix_manifest.json"
DOC = ROOT / "docs" / "PHASE25_SNAKEWAY_NPC_VARIANT_MATRIX.md"

MAP_TABLE_OFFSET = 0x0008E2E0
MAP_ENTRY_SIZE = 0x38
MAP_ENTRY_COUNT = 452
MAP_TABLE_LITERAL_REF = 0x00008A58
ORIGINAL_MAP_TABLE_VA = 0x0808E2E0
SNAKEWAY_MAP_ENTRY = 0

# Templates copied from native npcs_pointer examples collected in previous probes.
TEMPLATES = {
    "npc_map65_z2a33": bytes.fromhex(
        "E8 00 40 00 01 06 8C 01 28 F1 27 08 55 FD 00 08"
        "00 00 00 00 4C 00 00 00 60 00 78 00 BF 00 00 00"
    ),
    "npc_map141_z8a2": bytes.fromhex(
        "78 00 28 00 00 04 46 00 78 00 28 00 01 04 64 00"
        "78 00 28 00 02 75 7D 05 44 00 24 08 55 FD 00 08"
    ),
    "npc_map146_z8a7": bytes.fromhex(
        "D0 01 38 00 01 08 78 04 38 B0 23 08 55 FD 00 08"
        "A3 00 02 00 44 00 00 00 50 00 78 00 AD 00 00 00"
    ),
    "npc_map156_z8a17": bytes.fromhex(
        "E4 00 E0 00 01 06 55 01 84 EF 22 08 75 76 00 08"
        "6D 77 00 08 59 00 69 01 88 00 88 01 00 08 13 00"
    ),
}

POSITIONS_LINE = [(0x0048, 0x0058), (0x00A0, 0x0058), (0x0100, 0x0058), (0x01C0, 0x0058), (0x02C0, 0x0058), (0x03A0, 0x0058)]
POSITIONS_CLUSTER = [(0x0070, 0x0058), (0x0088, 0x0058), (0x00A0, 0x0058), (0x00B8, 0x0058)]

VARIANTS = [
    {
        "id": "v01_template65_line",
        "template": "npc_map65_z2a33",
        "positions": POSITIONS_LINE,
        "mutations": [],
        "purpose": "Control variant: native template 65 repeated across Snakeway.",
    },
    {
        "id": "v02_template65_actor297_u16_06",
        "template": "npc_map65_z2a33",
        "positions": POSITIONS_LINE,
        "mutations": [(0x06, "u16", 297)],
        "purpose": "Tests hypothesis: u16 @ 0x06 is actor/character id.",
    },
    {
        "id": "v03_template141_line",
        "template": "npc_map141_z8a2",
        "positions": POSITIONS_LINE,
        "mutations": [],
        "purpose": "Different native NPC template with multiple pointer-like fields.",
    },
    {
        "id": "v04_template146_cluster",
        "template": "npc_map146_z8a7",
        "positions": POSITIONS_CLUSTER,
        "mutations": [],
        "purpose": "Clusters a known NPC/object-like template near early Snakeway view.",
    },
    {
        "id": "v05_template156_actor297_u16_06",
        "template": "npc_map156_z8a17",
        "positions": POSITIONS_LINE,
        "mutations": [(0x06, "u16", 297)],
        "purpose": "Tests actor-id hypothesis on a template also seen near item-like records.",
    },
    {
        "id": "v06_template65_actor297_u16_0a",
        "template": "npc_map65_z2a33",
        "positions": POSITIONS_LINE,
        "mutations": [(0x0A, "u16", 297)],
        "purpose": "Tests alternate u16 slot 0x0A as actor/visual field.",
    },
]

TEXT_PATCHES = [
    (0x5DBD0, "Snakeway", "Riftway"),
    (0x5DF98, "Go to King Yemma's Castle", "Find Rift Gate Guide"),
    (0x5DFCC, "Train with Other World Fighters", "Choose Gateway Dimension"),
    (0x651E0, "Yemma's Assistant", "Rift Gate Guide"),
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


def align(v: int, boundary: int) -> int:
    return (v + boundary - 1) & ~(boundary - 1)


def append_bytes(data: bytearray, blob: bytes, alignment: int = 4) -> tuple[int, int]:
    off = align(len(data), alignment)
    data.extend(b"\xFF" * (off - len(data)))
    va = 0x08000000 + off
    data.extend(blob)
    return off, va


def read_u32(data: bytes | bytearray, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def write_u32(data: bytearray, off: int, val: int) -> None:
    struct.pack_into("<I", data, off, val)


def utf16z(text: str) -> bytes:
    return text.encode("utf-16le") + b"\x00\x00"


def apply_text_patch(data: bytearray, off: int, old: str, new: str) -> dict:
    old_raw = utf16z(old)
    if bytes(data[off:off + len(old_raw)]) != old_raw:
        raise SystemExit(f"Text precondition failed at 0x{off:06X}: expected {old!r}")
    if len(new) > len(old):
        raise SystemExit(f"Text too long at 0x{off:06X}: {new!r}")
    slot = bytearray(b"\x00" * len(old_raw))
    nr = utf16z(new)
    slot[:len(nr)] = nr
    data[off:off + len(slot)] = slot
    return {"offset": f"0x{off:06X}", "old": old, "new": new}


def checksum(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def mutate_record(template: bytes, x: int, y: int, mutations: list[tuple[int, str, int]]) -> bytes:
    rec = bytearray(template)
    struct.pack_into("<HH", rec, 0x00, x, y)
    for off, kind, value in mutations:
        if kind == "u16":
            struct.pack_into("<H", rec, off, value)
        elif kind == "u32":
            struct.pack_into("<I", rec, off, value)
        elif kind == "u8":
            rec[off] = value & 0xFF
        else:
            raise ValueError(kind)
    return bytes(rec)


def build_variant(base: bytes, variant: dict) -> dict:
    data = bytearray(base)
    applied = [apply_text_patch(data, *patch) for patch in TEXT_PATCHES]
    title = ("LOG4" + variant["id"][-8:].upper()).encode("ascii")[:12]
    data[0xA0:0xAC] = title.ljust(12, b"\0")
    data[0xBD] = checksum(data)

    npc_blob = b"".join(mutate_record(TEMPLATES[variant["template"]], x, y, variant["mutations"]) for x, y in variant["positions"])
    npc_off, npc_va = append_bytes(data, npc_blob, 4)

    extended = bytearray(base[MAP_TABLE_OFFSET:MAP_TABLE_OFFSET + MAP_ENTRY_COUNT * MAP_ENTRY_SIZE])
    snake = bytearray(extended[SNAKEWAY_MAP_ENTRY * MAP_ENTRY_SIZE:(SNAKEWAY_MAP_ENTRY + 1) * MAP_ENTRY_SIZE])
    snake[0x08] = len(variant["positions"])
    write_u32(snake, 0x20, npc_va)
    extended[SNAKEWAY_MAP_ENTRY * MAP_ENTRY_SIZE:(SNAKEWAY_MAP_ENTRY + 1) * MAP_ENTRY_SIZE] = snake
    table_off, table_va = append_bytes(data, bytes(extended), 4)
    if read_u32(data, MAP_TABLE_LITERAL_REF) != ORIGINAL_MAP_TABLE_VA:
        raise SystemExit("Unexpected map table literal")
    write_u32(data, MAP_TABLE_LITERAL_REF, table_va)
    data[0xBD] = checksum(data)
    while len(data) % 4:
        data.append(0)
    final = bytes(data)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gba = OUT_DIR / f"DBZ_LOG4_phase25_{variant['id']}.gba"
    ips = OUT_DIR / f"DBZ_LOG4_phase25_{variant['id']}.ips"
    txt = OUT_DIR / f"DBZ_LOG4_phase25_{variant['id']}.txt"
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    record = {
        **variant,
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "npc_array": {"offset": f"0x{npc_off:06X}", "va": f"0x{npc_va:08X}", "record_count": len(variant["positions"]), "record_size": 0x20},
        "extended_map_table": {"offset": f"0x{table_off:06X}", "va": f"0x{table_va:08X}"},
        "text_patches": applied,
    }
    txt.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base SHA-1 mismatch")
    records = [build_variant(base, variant) for variant in VARIANTS]
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({"schema": "jurai.phase25.snakeway_npc_variant_matrix.v1", "policy": "route_a_visual_confirmation_variants", "variants": records}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Phase 25 — Snakeway NPC variant matrix",
        "",
        "Route A: creates multiple NPC-record variants to manually identify which native entity fields control sprite visibility/interactability.",
        "",
        "## Variants",
        "",
    ]
    for r in records:
        lines.append(f"- `{r['id']}` — `{r['output_gba']}` — {r['purpose']} SHA-1 `{r['modified_sha1']}`")
    lines.extend(["", f"Manifest: `{MANIFEST.relative_to(ROOT)}`", ""])
    DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")
    print(f"Wrote {DOC.relative_to(ROOT)}")
    print(f"Generated {len(records)} variants in {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
