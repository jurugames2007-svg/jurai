#!/usr/bin/env python3
"""Phase 34: Gateway hook research package.

This phase turns the next native-script work into a concrete hook research
package. It does not pretend the menu is already interactable; instead it
records exact candidate text offsets, trigger strategy, and a safe debug ROM
that keeps Bubbles/Gateway text visible while native scripts are decoded.
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
OUT_DIR = ROOT / "additive_content" / "phase34_gateway_hook_research"
DOC = ROOT / "docs" / "PHASE34_GATEWAY_HOOK_RESEARCH.md"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase34_gateway_hook_research"
MAGIC = b"LOG4H34!"
VERSION = 1

CANDIDATES = [
    {"kind": "map_name", "offset": "0x05DBD0", "original": "Snakeway", "debug": "Bubbles", "reason": "visible early path label"},
    {"kind": "objective", "offset": "0x05DF98", "original": "Go to King Yemma's Castle", "debug": "Find Bubbles Gate", "reason": "first objective shown in journal"},
    {"kind": "objective", "offset": "0x05DFCC", "original": "Train with Other World Fighters", "debug": "Choose Bubbles Gate", "reason": "second objective / gateway hint"},
    {"kind": "chapter_title", "offset": "0x06B57C", "original": "Chapter 1", "debug": "Bubbles!", "reason": "chapter splash title"},
    {"kind": "chapter_subtitle", "offset": "0x06B590", "original": "The Other World", "debug": "Bubbles Gateway", "reason": "chapter splash subtitle"},
    {"kind": "npc_label", "offset": "0x0651E0", "original": "Yemma's Assistant", "debug": "Bubbles Guide", "reason": "known early NPC/database label replacement"},
    {"kind": "npc_desc", "offset": "0x065204", "original": "This assistant helps King Yemma usher souls into the Other World.", "debug": "Talk to Bubbles on Snakeway to open Super, GT, AF, LOG1 and LOG2.", "reason": "safe equal/shorter gateway explanation"},
]

HOOK_STEPS = [
    "Find code path that displays early Other World dialogue in EWRAM.",
    "Trace from visible dialogue buffer back to ROM script pointer.",
    "Replace one existing dialogue script branch with gateway text bank.",
    "Only after text branch is stable, add selection state machine.",
    "Keep original branch pointer as fallback if gateway hook flag is off.",
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


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base ROM SHA-1 mismatch")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    research = {
        "schema": "jurai.phase34.gateway_hook_research.v1",
        "policy": "research_payload_no_runtime_menu_hook_yet",
        "candidate_offsets": CANDIDATES,
        "hook_steps": HOOK_STEPS,
        "preferred_start": "reuse visible Bubbles Gateway debug text, then trace actual script pointer",
        "fallback": "phase26_bubbles_start_gateway ROM remains the stable debug build",
    }
    research_path = OUT_DIR / "gateway_hook_research.json"
    research_path.write_text(json.dumps(research, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    text_bank = OUT_DIR / "gateway_hook_text_bank.utf16le.bin"
    text_bank.write_bytes(("Bubbles: Choose a rift.\n-Super\n-GT\n-AF\n-LOG1 Dimension\n-LOG2 Dimension\n-End").encode("utf-16le") + b"\x00\x00")
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(research_path, research_path.relative_to(ROOT).as_posix())
        zf.write(text_bank, text_bank.relative_to(ROOT).as_posix())
    payload = bio.getvalue()
    directory = json.dumps({"schema": "jurai.phase34.payload.v1", "files": [research_path.relative_to(ROOT).as_posix(), text_bank.relative_to(ROOT).as_posix()], "payload_sha1": hashlib.sha1(payload).hexdigest()}, separators=(",", ":")).encode("utf-8")
    header = MAGIC + struct.pack("<III", VERSION, len(directory), len(payload))
    final = bytearray(base + header + directory + payload)
    while len(final) % 4:
        final.append(0)
    final = bytes(final)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    manifest = {"schema": "jurai.phase34.gateway_hook_research_build.v1", "output_gba": gba.relative_to(ROOT).as_posix(), "output_ips": ips.relative_to(ROOT).as_posix(), "modified_sha1": hashlib.sha1(final).hexdigest(), "research": research_path.relative_to(ROOT).as_posix()}
    (OUT_DIR / "phase34_gateway_hook_research_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text("# Phase 34 — Gateway hook research\n\n" +
                   "Prepared the concrete hook research package for turning the Bubbles debug text into a real in-game menu.\n\n" +
                   f"Output ROM: `{gba.relative_to(ROOT)}`\n\n" +
                   f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n\n" +
                   f"Research manifest: `{research_path.relative_to(ROOT)}`\n", encoding="utf-8")
    txt.write_text(DOC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {gba}")


if __name__ == "__main__":
    main()
