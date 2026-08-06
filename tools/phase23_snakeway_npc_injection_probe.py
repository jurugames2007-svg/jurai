#!/usr/bin/env python3
"""Phase 23: experimental Snakeway NPC injection probe.

This is the first attempt to place a native NPC/entity record directly on the
Snakeway map by extending the map-entry table and pointing Snakeway's appended
record at a copied native 0x20-byte NPC record. Original ROM/map-entry bytes are
not overwritten; only known table-base literals are redirected to the appended
extended table.

The NPC record format is still being reverse engineered. This build is for
runtime testing and may need iterative adjustment.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase23_snakeway_npc_probe"
MANIFEST = ROOT / "additive_content" / "gateway" / "phase23_snakeway_npc_probe_manifest.json"
DOC = ROOT / "docs" / "PHASE23_SNAKEWAY_NPC_PROBE.md"

MAP_TABLE_OFFSET = 0x0008E2E0
MAP_ENTRY_SIZE = 0x38
MAP_ENTRY_COUNT = 452
MAP_TABLE_LITERAL_REF = 0x00008A58
ORIGINAL_MAP_TABLE_VA = 0x0808E2E0
SNAKEWAY_MAP_ENTRY = 0

# Native NPC record copied from map 65 / Z2A33 and repositioned on Snakeway.
NPC_TEMPLATE = bytes.fromhex(
    "E8 00 40 00 01 06 8C 01 28 F1 27 08 55 FD 00 08"
    "00 00 00 00 4C 00 00 00 60 00 78 00 BF 00 00 00"
)

TEXT_PATCHES = [
    (0x5DBD0, "Snakeway", "Riftway"),
    (0x5DF98, "Go to King Yemma's Castle", "Find Rift Gate Guide"),
    (0x651E0, "Yemma's Assistant", "Rift Gate Guide"),
    (0x65204, "This assistant helps King Yemma usher souls into the Other World.", "Guide at Snakeway opens Super, GT, AF, LOG1 and LOG2."),
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


def read_u32(data: bytes | bytearray, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def write_u32(data: bytearray, off: int, val: int) -> None:
    struct.pack_into("<I", data, off, val)


def align(v: int, boundary: int) -> int:
    return (v + boundary - 1) & ~(boundary - 1)


def append_bytes(data: bytearray, blob: bytes, alignment: int = 4) -> tuple[int, int]:
    off = align(len(data), alignment)
    data.extend(b"\xFF" * (off - len(data)))
    va = 0x08000000 + off
    data.extend(blob)
    return off, va


def utf16z(s: str) -> bytes:
    return s.encode("utf-16le") + b"\x00\x00"


def apply_text_patch(data: bytearray, off: int, old: str, new: str) -> dict:
    old_raw = utf16z(old)
    if bytes(data[off:off+len(old_raw)]) != old_raw:
        raise SystemExit(f"Text precondition failed at 0x{off:06X}: {old!r}")
    if len(new) > len(old):
        raise SystemExit(f"Text too long at 0x{off:06X}: {new!r}")
    slot = bytearray(b"\x00" * len(old_raw))
    nr = utf16z(new)
    slot[:len(nr)] = nr
    data[off:off+len(slot)] = slot
    return {"offset": f"0x{off:06X}", "old": old, "new": new}


def header_checksum(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def make_npc_record() -> bytes:
    rec = bytearray(NPC_TEMPLATE)
    # Hypothesis: first two u16 are x/y pixel coordinates. Place near early Snakeway.
    struct.pack_into("<HH", rec, 0x00, 0x0100, 0x0058)
    return bytes(rec)


def main() -> None:
    base = BASE.read_bytes()
    base_sha1 = hashlib.sha1(base).hexdigest()
    if base_sha1 != BASE_SHA1:
        raise SystemExit(f"Base SHA-1 mismatch: {base_sha1}")
    data = bytearray(base)
    applied_text = [apply_text_patch(data, *patch) for patch in TEXT_PATCHES]
    data[0xA0:0xAC] = b"LOG4SWNPC23\0"  # 12 bytes.
    data[0xBD] = header_checksum(data)

    npc_off, npc_va = append_bytes(data, make_npc_record(), 4)
    extended = bytearray(base[MAP_TABLE_OFFSET:MAP_TABLE_OFFSET + MAP_ENTRY_COUNT * MAP_ENTRY_SIZE])
    snake = bytearray(extended[SNAKEWAY_MAP_ENTRY * MAP_ENTRY_SIZE:(SNAKEWAY_MAP_ENTRY + 1) * MAP_ENTRY_SIZE])
    snake[0x08] = 1  # npc_count
    write_u32(snake, 0x20, npc_va)
    extended[SNAKEWAY_MAP_ENTRY * MAP_ENTRY_SIZE:(SNAKEWAY_MAP_ENTRY + 1) * MAP_ENTRY_SIZE] = snake
    table_off, table_va = append_bytes(data, bytes(extended), 4)
    if read_u32(data, MAP_TABLE_LITERAL_REF) != ORIGINAL_MAP_TABLE_VA:
        raise SystemExit("Unexpected map table literal")
    write_u32(data, MAP_TABLE_LITERAL_REF, table_va)
    data[0xBD] = header_checksum(data)
    while len(data) % 4:
        data.append(0)
    final = bytes(data)

    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    manifest = {
        "schema": "jurai.phase23.snakeway_npc_probe.v1",
        "policy": "experimental_map_table_extension_original_map_table_preserved",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "snakeway_map_entry": SNAKEWAY_MAP_ENTRY,
        "npc_record": {"offset": f"0x{npc_off:06X}", "va": f"0x{npc_va:08X}", "size": 0x20, "template_source": "map65_Z2A33_native_npc_record"},
        "extended_map_table": {"offset": f"0x{table_off:06X}", "va": f"0x{table_va:08X}", "entry_count": MAP_ENTRY_COUNT},
        "text_patches": applied_text,
        "test_goal": "Start game, reach Riftway/Snakeway, see if native NPC record spawns without crash.",
        "fallback": "Use phase22 debug text build if entity probe crashes.",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Phase 23 — Snakeway NPC injection probe",
        "",
        "Experimental build that points the Snakeway map entry at a copied native NPC record.",
        "",
        f"Output ROM: `{gba.relative_to(ROOT)}`",
        f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`",
        f"NPC VA: `0x{npc_va:08X}`",
        f"Extended map table VA: `0x{table_va:08X}`",
        "",
        "If the map crashes, entity-record semantics need more decoding before real NPC insertion.",
    ]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {gba}")
    print(f"Wrote {ips}")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
