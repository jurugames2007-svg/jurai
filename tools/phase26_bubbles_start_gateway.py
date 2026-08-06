#!/usr/bin/env python3
"""Phase 26: Bubbles start gateway debug build.

This is a safe, visible gateway trigger concept for immediate testing. Instead
of risking unstable native NPC/entity bytecode, it reuses confirmed early-game
text surfaces (chapter, objective, NPC labels/database text) so the player sees
Bubbles as the Rift Gate guide from the beginning.

Canonical builds remain original-first. This debug build is for fast testing.
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
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase26_bubbles_start_gateway"
MANIFEST = ROOT / "additive_content" / "gateway" / "phase26_bubbles_start_gateway_manifest.json"
DOC = ROOT / "docs" / "PHASE26_BUBBLES_START_GATEWAY.md"
MAGIC = b"LOG4BB26"
VERSION = 1

@dataclass(frozen=True)
class TextPatch:
    offset: int
    old: str
    new: str
    note: str

PATCHES = [
    TextPatch(0x5DBD0, "Snakeway", "Bubbles", "start map/debug label"),
    TextPatch(0x5DE1C, "Other World Saga", "Bubbles Saga", "saga label"),
    TextPatch(0x5DF98, "Go to King Yemma's Castle", "Find Bubbles Gate", "first objective"),
    TextPatch(0x5DFCC, "Train with Other World Fighters", "Choose Bubbles Gate", "second objective"),
    TextPatch(0x6B57C, "Chapter 1", "Bubbles!", "chapter title"),
    TextPatch(0x6B590, "The Other World", "Bubbles Gateway", "chapter subtitle"),
    TextPatch(0x6513C, "King Yemma", "Bubbles", "NPC/database label"),
    TextPatch(0x65152, "King Yemma is a giant ogre who guards the entrance to the Other World.", "Bubbles guards the gate to Super, GT, AF, LOG1 and LOG2.", "database description"),
    TextPatch(0x651E0, "Yemma's Assistant", "Bubbles Guide", "NPC/database label"),
    TextPatch(0x65204, "This assistant helps King Yemma usher souls into the Other World.", "Talk to Bubbles on Snakeway to open Super, GT, AF, LOG1 and LOG2.", "NPC/database description"),
    TextPatch(0x64A44, "Bubbles is an ape who hangs out with King Kai.", "Bubbles helps open the Rift Gate.", "Bubbles database description"),
]

CONTRACT = {
    "schema": "jurai.phase26.bubbles_start_gateway.v1",
    "mode": "debug_visible_text_trigger",
    "npc": "Bubbles",
    "location": "start / Snakeway / Bubbles Gateway",
    "routes": ["SUPER_ROUTE", "GT_ROUTE", "AF_ROUTE", "LOG1_DIMENSION", "LOG2_DIMENSION"],
    "goal": "Make the intended gateway visible at the beginning while native NPC interaction bytecode is still being decoded.",
    "canonical_note": "Use phase19/20 for original-first story. This build is explicit debug/testing.",
}


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
    old_raw = utf16z(patch.old)
    current = bytes(data[patch.offset:patch.offset + len(old_raw)])
    if current != old_raw:
        raise SystemExit(f"Text precondition failed at 0x{patch.offset:06X}: expected {patch.old!r}")
    if len(patch.new) > len(patch.old):
        raise SystemExit(f"New text too long at 0x{patch.offset:06X}: {patch.new!r} > {patch.old!r}")
    slot = bytearray(b"\x00" * len(old_raw))
    new_raw = utf16z(patch.new)
    slot[:len(new_raw)] = new_raw
    data[patch.offset:patch.offset + len(slot)] = slot
    return {"offset": f"0x{patch.offset:06X}", "old": patch.old, "new": patch.new, "note": patch.note}


def header_checksum(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def payload_zip(files: list[Path]) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            if path.exists():
                zf.write(path, path.relative_to(ROOT).as_posix())
    return bio.getvalue()


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base SHA-1 mismatch")
    data = bytearray(base)
    applied = [apply_patch(data, p) for p in PATCHES]
    data[0xA0:0xAC] = b"LOG4BUBBLES\0"  # exactly 12 bytes
    data[0xBD] = header_checksum(data)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    contract_path = ROOT / "additive_content" / "gateway" / "bubbles_start_gateway_contract.json"
    contract_path.write_text(json.dumps(CONTRACT, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    dialogue_bank = ROOT / "additive_content" / "gateway" / "bubbles_gateway_dialogue.utf16le.bin"
    dialogue_text = "Bubbles: Choose a rift. Super, GT, AF, LOG1, or LOG2."
    dialogue_bank.write_bytes(utf16z(dialogue_text))
    payload = payload_zip([contract_path, dialogue_bank])
    directory = json.dumps({"schema": "jurai.phase26.payload.v1", "files": [contract_path.relative_to(ROOT).as_posix(), dialogue_bank.relative_to(ROOT).as_posix()], "payload_sha1": hashlib.sha1(payload).hexdigest()}, separators=(",", ":")).encode("utf-8")
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
        "schema": "jurai.phase26.bubbles_start_gateway_build.v1",
        "policy": "safe_debug_text_trigger_native_npc_hook_pending",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "text_patches": applied,
        "contract": contract_path.relative_to(ROOT).as_posix(),
        "dialogue_bank": dialogue_bank.relative_to(ROOT).as_posix(),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Phase 26 — Bubbles Start Gateway",
        "",
        "Safe debug build that makes Bubbles the visible gateway guide at the start of the game.",
        "Native NPC interaction bytecode is still pending, but this build is deterministic and easy to test.",
        "",
        f"Output ROM: `{gba.relative_to(ROOT)}`",
        f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`",
        "",
        "## Patches",
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
