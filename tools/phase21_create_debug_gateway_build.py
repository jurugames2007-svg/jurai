#!/usr/bin/env python3
"""Phase 21.1: debug gateway build.

This creates an OPTIONAL debug ROM that deliberately changes a few early UTF-16
strings so testers can see the gateway/debug route concept immediately. It is
not the canonical story build; phase19/20 remain original-first.
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase21_debug_gateway_build"
MANIFEST = ROOT / "additive_content" / "gateway" / "phase21_debug_gateway_manifest.json"
DOC = ROOT / "docs" / "PHASE21_DEBUG_GATEWAY_BUILD.md"
MAGIC = b"LOG4DG21"
VERSION = 1

@dataclass(frozen=True)
class Patch:
    offset: int
    old: str
    new: str
    note: str

PATCHES = [
    Patch(0x579E4, "Select Game", "Rift Gate", "save/select screen label"),
    Patch(0x579FC, "New Game", "Gateway", "new game label in debug build"),
    Patch(0x58168, "No Saved Games", "Route Select", "no save label"),
    Patch(0x6B57C, "Chapter 1", "RIFT GATE", "chapter overlay debug"),
    Patch(0x6B708, "Chapter 10", "RIFT GATE", "chapter overlay debug duplicate"),
    Patch(0x6B72C, "Chapter 11", "RIFT GATE", "chapter overlay debug duplicate"),
    Patch(0x6B752, "Chapter 12", "RIFT GATE", "chapter overlay debug duplicate"),
    Patch(0x6B590, "The Other World", "Post Kid Buu", "chapter subtitle debug"),
    Patch(0x5DC32, "The Other World", "Rift Gateway", "map/name debug"),
]

PAYLOAD_FILES = [
    ROOT / "additive_content" / "gateway" / "postgame_dimension_gateway.json",
    ROOT / "additive_content" / "gateway" / "gateway_menu_layout.json",
    ROOT / "additive_content" / "gateway" / "gateway_state_machine.json",
    ROOT / "additive_content" / "gateway" / "route_start_profiles.json",
    ROOT / "additive_content" / "playability" / "canonical_line.json",
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


def utf16z(text: str) -> bytes:
    return text.encode("utf-16le") + b"\x00\x00"


def apply_text_patch(data: bytearray, patch: Patch) -> dict:
    old = utf16z(patch.old)
    cur = bytes(data[patch.offset : patch.offset + len(old)])
    if cur != old:
        raise SystemExit(f"precondition failed at 0x{patch.offset:06X}: {patch.old!r}")
    if len(patch.new) > len(patch.old):
        raise SystemExit(f"new text too long at 0x{patch.offset:06X}: {patch.new}")
    slot = bytearray(b"\x00" * len(old))
    new = utf16z(patch.new)
    slot[: len(new)] = new
    data[patch.offset : patch.offset + len(slot)] = slot
    return {"offset": f"0x{patch.offset:06X}", "old": patch.old, "new": patch.new, "note": patch.note}


def header_checksum(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def payload_zip() -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in PAYLOAD_FILES:
            if p.exists():
                zf.write(p, p.relative_to(ROOT).as_posix())
    return bio.getvalue()


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base SHA-1 mismatch")
    data = bytearray(base)
    applied = [apply_text_patch(data, p) for p in PATCHES]
    data[0xA0:0xAC] = b"LOG4DEBUG21\0"  # exactly 12-byte GBA title field.
    data[0xBD] = header_checksum(data)
    payload = payload_zip()
    directory = json.dumps({"schema": "jurai.phase21.debug_gateway_payload.v1", "payload_sha1": hashlib.sha1(payload).hexdigest(), "files": [p.relative_to(ROOT).as_posix() for p in PAYLOAD_FILES if p.exists()]}, separators=(",", ":")).encode("utf-8")
    header = MAGIC + struct.pack("<III", VERSION, len(directory), len(payload))
    data.extend(header + directory + payload)
    while len(data) % 4:
        data.append(0)
    final = bytes(data)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    manifest = {
        "schema": "jurai.phase21.debug_gateway_build.v1",
        "policy": "optional_debug_build_not_canonical_original_first",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "text_patches": applied,
        "warning": "This build intentionally changes early text for debug visibility. Use phase19/20 for original-first line.",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Phase 21.1 — Debug gateway build",
        "",
        "Optional debug build for quickly seeing gateway labels from the start.",
        "This is not the canonical original-first story ROM.",
        "",
        f"Output ROM: `{gba.relative_to(ROOT)}`",
        f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`",
        "",
        "## Text patches",
        "",
    ]
    for item in applied:
        lines.append(f"- {item['offset']}: `{item['old']}` -> `{item['new']}` ({item['note']})")
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {gba}")
    print(f"Wrote {ips}")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
