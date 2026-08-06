#!/usr/bin/env python3
"""Phase 19: postgame/dimension gateway scaffold.

Creates the playable-line contract requested by the user:
  Buu's Fury original -> post-Kid-Buu Super/GT/AF -> pre-Kid-Buu LOG1/LOG2 dimensions.

This phase is intentionally original-first and append-only: it appends the
contract/gateway data to a clean Buu's Fury ROM and leaves the base experience
unchanged until a later event-hook phase unlocks the gateway in-game.
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase19_postgame_dimension_gateway"
PLAY = ROOT / "additive_content" / "playability"
GATE = ROOT / "additive_content" / "gateway"
DOC = ROOT / "docs" / "PHASE19_POSTGAME_DIMENSION_GATEWAY.md"
MANIFEST = GATE / "postgame_dimension_gateway_payload_manifest.json"
MAGIC = b"LOG4GW19"
VERSION = 1


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


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_contracts() -> list[Path]:
    canonical = {
        "schema": "jurai.phase19.canonical_line.v1",
        "main_line": [
            {"order": 1, "id": "BUUS_FURY_MAIN", "label": "Original Dragon Ball Z: Buu's Fury", "position": "mainline through Kid Buu", "runtime_policy": "unchanged early game"},
            {"order": 2, "id": "POST_KID_BUU_EXPANSION", "label": "Post Kid Buu: Super / GT / AF", "position": "after original ending", "routes": ["SUPER_ROUTE", "GT_ROUTE", "AF_ROUTE"]},
            {"order": 3, "id": "PRE_KID_BUU_DIMENSIONS", "label": "Pre Kid Buu dimensions: LOG1 / LOG2", "position": "memory dimensions accessible after gateway", "dimensions": ["LOG1_DIMENSION", "LOG2_DIMENSION"]},
        ],
        "rule": "Story mode starts with Buu's Fury. Expansion/dimension starts are unlocked after Kid Buu or through debug gateway.",
    }
    gateway = {
        "schema": "jurai.phase19.dimension_gateway.v1",
        "gateway_id": "CAPSULE_CORP_RIFT_GATEWAY",
        "location_plan": "Capsule Corp / Rift Lab, unlocked after Kid Buu or in debug builds",
        "unlock_flags": ["STORY_KID_BUU_DEFEATED", "LOG4_POSTGAME_GATEWAY_UNLOCKED"],
        "debug_unlock_flag": "LOG4_DEBUG_GATEWAY_UNLOCKED",
        "entries": [
            {"entry_id": "GATE_SUPER", "label": "Dragon Ball Super", "target": "SUPER_ROUTE", "timeline": "post Kid Buu", "status": "payload_ready_event_hook_pending"},
            {"entry_id": "GATE_GT", "label": "Dragon Ball GT", "target": "GT_ROUTE", "timeline": "post Kid Buu alternate branch", "status": "payload_ready_event_hook_pending"},
            {"entry_id": "GATE_AF", "label": "Dragon Ball AF", "target": "AF_ROUTE", "timeline": "post GT/Super rift fan branch", "status": "payload_ready_event_hook_pending"},
            {"entry_id": "GATE_LOG1", "label": "The Legacy of Goku Dimension", "target": "LOG1_DIMENSION", "timeline": "pre Kid Buu memory dimension", "status": "payload_ready_event_hook_pending"},
            {"entry_id": "GATE_LOG2", "label": "The Legacy of Goku II Dimension", "target": "LOG2_DIMENSION", "timeline": "pre Kid Buu memory dimension", "status": "payload_ready_event_hook_pending"},
        ],
        "menu_style": {"screen": [240, 160], "tile": [8, 8], "portrait": [40, 40], "font": "reuse native Buu's Fury UI/font"},
    }
    flags = {
        "schema": "jurai.phase19.gateway_flags.v1",
        "flags": [
            "STORY_KID_BUU_DEFEATED",
            "LOG4_POSTGAME_GATEWAY_UNLOCKED",
            "LOG4_DEBUG_GATEWAY_UNLOCKED",
            "LOG4_ROUTE_SUPER_UNLOCKED",
            "LOG4_ROUTE_GT_UNLOCKED",
            "LOG4_ROUTE_AF_UNLOCKED",
            "DIM_LOG1_UNLOCKED",
            "DIM_LOG2_UNLOCKED",
        ],
        "status": "reserved_not_mapped_to_save_yet",
    }
    dimensions = {
        "schema": "jurai.phase19.log_dimensions.v1",
        "dimensions": [
            {"id": "LOG1_DIMENSION", "source_style": "The Legacy of Goku 1", "runtime_screen": [240, 160], "tile": [8, 8], "actor_cell": [40, 40], "boss_cell": [72, 72], "role": "pre Kid Buu memory dimension"},
            {"id": "LOG2_DIMENSION", "source_style": "The Legacy of Goku 2", "runtime_screen": [240, 160], "tile": [8, 8], "actor_cell": [40, 40], "boss_cell": [72, 72], "role": "pre Kid Buu memory dimension"},
        ],
    }
    paths = []
    for path, data in [
        (PLAY / "canonical_line.json", canonical),
        (GATE / "postgame_dimension_gateway.json", gateway),
        (GATE / "gateway_flags.json", flags),
        (GATE / "log_dimensions_profile.json", dimensions),
    ]:
        write_json(path, data)
        paths.append(path)
    return paths


def zip_payload(paths: list[Path]) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in paths:
            zf.write(path, path.relative_to(ROOT).as_posix())
    return bio.getvalue()


def main() -> None:
    base = BASE.read_bytes()
    sha = hashlib.sha1(base).hexdigest()
    if sha != BASE_SHA1:
        raise SystemExit(f"Base SHA-1 mismatch: {sha}")
    paths = build_contracts()
    payload = zip_payload(paths)
    directory = json.dumps({"schema": "jurai.phase19.gateway_payload_directory.v1", "files": [p.relative_to(ROOT).as_posix() for p in paths], "payload_sha1": hashlib.sha1(payload).hexdigest()}, separators=(",", ":")).encode("utf-8")
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
        "schema": "jurai.phase19.gateway_payload_build.v1",
        "policy": "append_only_original_early_game_unchanged",
        "base_sha1": sha,
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(modified_bytes).hexdigest(),
        "payload_offset": len(base) + len(header) + len(directory),
        "payload_size": len(payload),
        "files": [p.relative_to(ROOT).as_posix() for p in paths],
    }
    write_json(MANIFEST, manifest)
    lines = [
        "# Phase 19 — Postgame Dimension Gateway",
        "",
        "Created an append-only gateway contract for the requested playable line:",
        "",
        "```text",
        "Buu's Fury original -> post Kid Buu Super/GT/AF -> pre Kid Buu LOG1/LOG2 dimensions",
        "```",
        "",
        "## Outputs",
        "",
        f"- `{gba.relative_to(ROOT)}`",
        f"- `{ips.relative_to(ROOT)}`",
        f"- `{MANIFEST.relative_to(ROOT)}`",
        "",
        f"Modified SHA-1: `{hashlib.sha1(modified_bytes).hexdigest()}`",
        "",
        "## Runtime policy",
        "",
        "The early original game remains unchanged. The gateway is data-only until a later event hook unlocks it after Kid Buu or through debug.",
    ]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {gba}")
    print(f"Wrote {ips}")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
