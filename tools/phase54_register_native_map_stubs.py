#!/usr/bin/env python3
"""Phase 54: register additive native map stubs behind the playable Gateway.

This combines the Phase 51 boot Gateway/warp-room build with an extended native
AreaEntry table.  It appends five new AreaEntry records for SUPER/GT/AF/LOG1/LOG2
route IDs, redirects the native lookup literal to the appended table, and patches
the native AreaEntry count function from 452 to 457.

This does not yet make Gateway selections call the native map constructor.  It is
the safe registry step before that: the new IDs are now resolvable by the native
lookup function without replacing original entries.
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
PHASE51_SCRIPT = ROOT / "tools" / "phase51_boot_gateway_warp_rooms.py"
PHASE51_ROM = ROOT / "patch_output" / "DBZ_LOG4_phase51_boot_gateway_warp_rooms.gba"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase54_gateway_native_map_registry"
DOC = ROOT / "docs" / "PHASE54_GATEWAY_NATIVE_MAP_REGISTRY.md"
MANIFEST = ROOT / "additive_content" / "phase54_native_map_registry" / "phase54_gateway_native_map_registry_manifest.json"

MAP_TABLE_OFFSET = 0x0008E2E0
MAP_ENTRY_SIZE = 0x38
MAP_ENTRY_COUNT_ORIGINAL = 452
MAP_TABLE_LITERAL_REF = 0x00008A58
ORIGINAL_MAP_TABLE_VA = 0x0808E2E0
COUNT_FUNC_OFF = 0x000125E0
COUNT_FUNC_EXPECTED = bytes.fromhex("ff 20 c5 30 70 47")  # return 452
COUNT_FUNC_PATCH = bytes.fromhex("ff 20 ca 30 70 47")     # return 457

# New route IDs. These are intentionally outside known original story IDs.
# Entries are cloned from safe pairs observed by the Phase 53 trace, then their
# first two ID bytes are changed to the new route ID.
STUBS = [
    {"route": "SUPER", "new_pair": (0xF0, 0x01), "clone_pair": (0x00, 0x02), "label": "post Kid Buu gods safe stub"},
    {"route": "GT", "new_pair": (0xF0, 0x02), "clone_pair": (0x00, 0x04), "label": "Black Star/Baby safe stub"},
    {"route": "AF", "new_pair": (0xF0, 0x03), "clone_pair": (0x00, 0x05), "label": "SSJ5/Xicor safe stub"},
    {"route": "LOG1_DIM", "new_pair": (0xF0, 0x04), "clone_pair": (0x00, 0x60), "label": "LOG1 Saiyan/Namek memory safe stub"},
    {"route": "LOG2_DIM", "new_pair": (0xF0, 0x05), "clone_pair": (0x00, 0x62), "label": "LOG2 Android/Cell memory safe stub"},
]


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def hchk(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def align(v: int, boundary: int) -> int:
    return (v + boundary - 1) & ~(boundary - 1)


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


def find_entry(table: bytes, pair: tuple[int, int]) -> tuple[int, bytes]:
    for i in range(MAP_ENTRY_COUNT_ORIGINAL):
        off = i * MAP_ENTRY_SIZE
        if table[off] == pair[0] and table[off + 1] == pair[1]:
            return i, table[off:off + MAP_ENTRY_SIZE]
    raise KeyError(f"Could not find AreaEntry pair {pair[0]:02X}:{pair[1]:02X}")


def build_phase51() -> None:
    subprocess.run([sys.executable, str(PHASE51_SCRIPT)], cwd=ROOT, check=True)


def main() -> int:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base ROM SHA-1 mismatch")
    build_phase51()
    if not PHASE51_ROM.exists():
        raise SystemExit("Missing Phase 51 ROM")

    data = bytearray(PHASE51_ROM.read_bytes())
    if struct.unpack_from("<I", data, MAP_TABLE_LITERAL_REF)[0] != ORIGINAL_MAP_TABLE_VA:
        raise SystemExit("Unexpected map table literal before registry patch")
    if bytes(data[COUNT_FUNC_OFF:COUNT_FUNC_OFF + len(COUNT_FUNC_EXPECTED)]) != COUNT_FUNC_EXPECTED:
        raise SystemExit("Unexpected native count function bytes")

    original_table = base[MAP_TABLE_OFFSET:MAP_TABLE_OFFSET + MAP_ENTRY_COUNT_ORIGINAL * MAP_ENTRY_SIZE]
    extended = bytearray(original_table)
    stub_manifest = []
    for stub in STUBS:
        clone_index, clone = find_entry(original_table, stub["clone_pair"])  # type: ignore[arg-type]
        rec = bytearray(clone)
        new_a, new_b = stub["new_pair"]  # type: ignore[misc]
        rec[0] = new_a
        rec[1] = new_b
        extended.extend(rec)
        stub_manifest.append({
            "route": stub["route"],
            "new_pair": f"{new_a:02X}:{new_b:02X}",
            "clone_pair": f"{stub['clone_pair'][0]:02X}:{stub['clone_pair'][1]:02X}",
            "clone_index": clone_index,
            "new_index": MAP_ENTRY_COUNT_ORIGINAL + len(stub_manifest),
            "label": stub["label"],
        })

    table_off = align(len(data), 4)
    data.extend(b"\xFF" * (table_off - len(data)))
    table_va = 0x08000000 + table_off
    data.extend(extended)

    struct.pack_into("<I", data, MAP_TABLE_LITERAL_REF, table_va)
    data[COUNT_FUNC_OFF:COUNT_FUNC_OFF + len(COUNT_FUNC_PATCH)] = COUNT_FUNC_PATCH
    data[0xA0:0xAC] = b"LOG4MAP54\0\0\0"
    data[0xBD] = hchk(data)
    while len(data) % 4:
        data.append(0)
    final = bytes(data)

    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))

    manifest = {
        "schema": "jurai.phase54.gateway_native_map_registry.v1",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "base_sha1": BASE_SHA1,
        "source_phase51_rom_sha1": sha1(PHASE51_ROM),
        "native_registry_status": "registered_not_warped",
        "map_table_literal_ref": f"0x{MAP_TABLE_LITERAL_REF:06X}",
        "extended_map_table_va": f"0x{table_va:08X}",
        "extended_map_table_offset": f"0x{table_off:06X}",
        "original_entry_count": MAP_ENTRY_COUNT_ORIGINAL,
        "new_entry_count": MAP_ENTRY_COUNT_ORIGINAL + len(STUBS),
        "count_function_patch": {"offset": f"0x{COUNT_FUNC_OFF:06X}", "old_return": 452, "new_return": MAP_ENTRY_COUNT_ORIGINAL + len(STUBS)},
        "stubs": stub_manifest,
        "playable_layer": "Phase 51 boot Gateway playable warp rooms retained",
        "limitation": "Gateway options still enter debug rooms. The native IDs are registered for the next hook but are not invoked by the Gateway yet.",
        "safety": "Original AreaEntry records are copied unchanged before appended stubs; original lookups still resolve to original entries first.",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = (
        "# Phase 54 — Gateway native map registry\n\n"
        "Phase 54 keeps the playable Phase 51 boot Gateway/warp rooms and additionally registers five additive native AreaEntry stubs for future real map-loader warps.\n\n"
        f"- Output ROM: `{gba.relative_to(ROOT)}`\n"
        f"- Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n"
        f"- Extended AreaEntry table VA: `0x{table_va:08X}`\n"
        f"- Native AreaEntry count: `452 -> {MAP_ENTRY_COUNT_ORIGINAL + len(STUBS)}`\n\n"
        "## Registered native IDs\n\n"
        "| Route | New pair | Cloned safe pair | Original clone index |\n"
        "|---|---:|---:|---:|\n"
        + "".join(f"| {s['route']} | `{s['new_pair']}` | `{s['clone_pair']}` | {s['clone_index']} |\n" for s in stub_manifest)
        + "\n## What this means\n\n"
        "The engine's native AreaEntry lookup can now resolve route-specific IDs (`F0:01` through `F0:05`) if a future hook asks for them. This is the registry step needed before making the boot Gateway call or steer the native map constructor.\n\n"
        "## What is still pending\n\n"
        "Gateway selections still open the Phase 51 debug rooms, not native Buu's Fury maps. The next hook must enter original engine initialization and then invoke/steer the native map constructor around `0x08009030` using either a known safe original pair or one of these appended `F0:*` route IDs.\n\n"
        "## Safety\n\n"
        "Original AreaEntry records are copied unchanged before the new stubs. Existing lookups still find the original entries first. Original fallback remains available from the Gateway via Start/ORIG.\n"
    )
    DOC.write_text(doc, encoding="utf-8")
    txt.write_text(doc, encoding="utf-8")
    print(f"Wrote {gba.relative_to(ROOT)}")
    print(f"SHA-1 {hashlib.sha1(final).hexdigest()}")
    print(f"Registered {len(STUBS)} native stubs at 0x{table_va:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
