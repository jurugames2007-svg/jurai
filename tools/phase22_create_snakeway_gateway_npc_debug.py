#!/usr/bin/env python3
"""Phase 22: Snakeway gateway NPC debug build.

Goal requested by user: place/represent an NPC on Snakeway that lets the player
navigate dimensions. The native NPC record hook is not fully decoded yet, so
this debug build makes the concept visible through safe early text patches and
an appended Snakeway Gatekeeper contract. It preserves the canonical phase19/20
original-first builds separately.
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
GATE = ROOT / "additive_content" / "gateway"
DOC = ROOT / "docs" / "PHASE22_SNAKEWAY_GATEKEEPER_DEBUG.md"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase22_snakeway_gatekeeper_debug"
MANIFEST = GATE / "phase22_snakeway_gatekeeper_manifest.json"
MAGIC = b"LOG4SW22"
VERSION = 1

@dataclass(frozen=True)
class TextPatch:
    offset: int
    old: str
    new: str
    note: str

# Equal/shorter UTF-16LE patches only.
PATCHES = [
    TextPatch(0x5DBD0, "Snakeway", "Riftway", "map name debug"),
    TextPatch(0x5DE1C, "Other World Saga", "Rift Gate Saga", "saga label debug"),
    TextPatch(0x5DF98, "Go to King Yemma's Castle", "Find Rift Gate Guide", "objective debug"),
    TextPatch(0x5DFCC, "Train with Other World Fighters", "Choose Gateway Dimension", "objective debug"),
    TextPatch(0x6B57C, "Chapter 1", "Rift Gate", "chapter title debug"),
    TextPatch(0x6B590, "The Other World", "Snakeway Gate", "chapter subtitle debug"),
    TextPatch(0x6513C, "King Yemma", "Gate Guide", "encyclopedia/NPC label debug"),
    TextPatch(0x651E0, "Yemma's Assistant", "Rift Gate Guide", "NPC label debug"),
    TextPatch(0x65204, "This assistant helps King Yemma usher souls into the Other World.", "Guide at Snakeway opens Super, GT, AF, LOG1 and LOG2.", "NPC description debug"),
]

OPTIONS = ["SUPER_ROUTE", "GT_ROUTE", "AF_ROUTE", "LOG1_DIMENSION", "LOG2_DIMENSION"]


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


def apply_patch(data: bytearray, patch: TextPatch) -> dict:
    old = utf16z(patch.old)
    current = bytes(data[patch.offset:patch.offset + len(old)])
    if current != old:
        raise SystemExit(f"Text precondition failed at 0x{patch.offset:06X}: expected {patch.old!r}")
    if len(patch.new) > len(patch.old):
        raise SystemExit(f"Patch too long at 0x{patch.offset:06X}: {patch.new!r} > {patch.old!r}")
    slot = bytearray(b"\x00" * len(old))
    new = utf16z(patch.new)
    slot[:len(new)] = new
    data[patch.offset:patch.offset + len(slot)] = slot
    return {"offset": f"0x{patch.offset:06X}", "old": patch.old, "new": patch.new, "note": patch.note}


def header_checksum(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def write_contracts() -> list[Path]:
    GATE.mkdir(parents=True, exist_ok=True)
    contract = {
        "schema": "jurai.phase22.snakeway_gatekeeper.v1",
        "policy": "debug_visible_contract_native_npc_hook_pending",
        "npc": {
            "id": "SNAKEWAY_RIFT_GATE_GUIDE",
            "display_name": "Rift Gate Guide",
            "intended_map": "Snakeway / Riftway",
            "intended_role": "dimension navigator NPC",
            "native_hook_status": "pending_entity_record_decode",
        },
        "dialogue": [
            {"id": "SW_GATE_HELLO", "speaker": "Rift Gate Guide", "text": "The road bends through time. Choose a dimension."},
            {"id": "SW_GATE_SUPER", "speaker": "Rift Gate Guide", "text": "Super opens after Kid Buu. Gods and universes wait."},
            {"id": "SW_GATE_GT", "speaker": "Rift Gate Guide", "text": "GT follows the Black Star trail."},
            {"id": "SW_GATE_AF", "speaker": "Rift Gate Guide", "text": "AF is a dangerous fan rift. Enter only when ready."},
            {"id": "SW_GATE_LOG1", "speaker": "Rift Gate Guide", "text": "LOG1 is a memory of Saiyan and Namek battles."},
            {"id": "SW_GATE_LOG2", "speaker": "Rift Gate Guide", "text": "LOG2 is a memory of Androids and Cell."},
        ],
        "options": OPTIONS,
        "unlock": {"debug": "LOG4_DEBUG_GATEWAY_UNLOCKED", "story": "STORY_KID_BUU_DEFEATED"},
        "next_native_tasks": [
            "Decode entity record field for visual actor ID.",
            "Create native NPC on Snakeway using Rift Gate Guide dialogue.",
            "Bind option selection to route/dimension starts.",
        ],
    }
    cpath = GATE / "snakeway_gatekeeper_contract.json"
    cpath.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # UTF-16LE dialogue bank for future native text hook.
    blob = bytearray()
    index = []
    for line in contract["dialogue"]:
        offset = len(blob)
        text = f"{line['speaker']}: {line['text']}"
        blob.extend(text.encode("utf-16le"))
        blob.extend(b"\x00\x00")
        index.append({"id": line["id"], "offset": offset, "bytes": len(text.encode("utf-16le")) + 2, "text": text})
    bpath = GATE / "snakeway_gatekeeper_dialogue.utf16le.bin"
    ipath = GATE / "snakeway_gatekeeper_dialogue_index.json"
    bpath.write_bytes(bytes(blob))
    ipath.write_text(json.dumps({"schema": "jurai.phase22.snakeway_dialogue_index.v1", "strings": index}, indent=2) + "\n", encoding="utf-8")
    return [cpath, bpath, ipath]


def payload_zip(paths: list[Path]) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in paths:
            zf.write(p, p.relative_to(ROOT).as_posix())
    return bio.getvalue()


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base SHA-1 mismatch")
    data = bytearray(base)
    applied = [apply_patch(data, p) for p in PATCHES]
    data[0xA0:0xAC] = b"LOG4SWGATE\0\0"  # 12-byte title.
    data[0xBD] = header_checksum(data)
    files = write_contracts()
    payload = payload_zip(files)
    directory = json.dumps({"schema": "jurai.phase22.snakeway_payload.v1", "files": [f.relative_to(ROOT).as_posix() for f in files], "payload_sha1": hashlib.sha1(payload).hexdigest()}, separators=(",", ":")).encode("utf-8")
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
        "schema": "jurai.phase22.snakeway_debug_build.v1",
        "policy": "debug_build_text_visible_native_npc_hook_pending",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "text_patches": applied,
        "payload_files": [f.relative_to(ROOT).as_posix() for f in files],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Phase 22 — Snakeway Gateway NPC debug",
        "",
        "Creates a debug-visible Rift Gate Guide concept for Snakeway/Riftway.",
        "Native NPC/entity hook is still pending, but text/contract/payload are now ready.",
        "",
        f"Output ROM: `{gba.relative_to(ROOT)}`",
        f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`",
        "",
        "## Text patches",
        "",
    ]
    for p in applied:
        lines.append(f"- {p['offset']}: `{p['old']}` -> `{p['new']}` ({p['note']})")
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {gba}")
    print(f"Wrote {ips}")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
