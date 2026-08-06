#!/usr/bin/env python3
"""Phase 39: package dialogue/IWRAM trace findings for Gateway hook work."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "additive_content" / "phase39_dialogue_trace"
DOC = ROOT / "docs" / "PHASE39_DIALOGUE_TRACE_PACKAGE.md"
ROM = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"

FINDINGS = {
    "schema": "jurai.phase39.dialogue_trace.v1",
    "policy": "analysis_only_no_rom_write",
    "target_goal": "Convert visible Bubbles/Gate Guide text into a real gateway menu hook.",
    "runtime_observations": {
        "ewram_dialog_buffer_region_a": "0x0202DB00-0x0202E300",
        "ewram_dialog_buffer_region_b": "0x0202C000-0x0202C200",
        "writer_iwram_pc_main": "0x03000268",
        "writer_iwram_pc_literal": "0x03000060",
        "rom_source_for_iwram_03000268_exact32": "0x007B7C0C",
        "rom_source_for_iwram_03000060_exact32": "0x007B7A04",
        "meaning": "dialogue text is written through an IWRAM decompression/copy routine; raw early dialogue strings are not directly present as simple UTF-16 in ROM.",
    },
    "watch_scripts": [
        "tools/gba_headless/watch_dialog_writes.mjs",
        "tools/gba_headless/watch_long_dialog_writes.mjs",
        "tools/gba_headless/disasm_iwram.mjs",
        "tools/gba_headless/snapshot_iwram.mjs",
    ],
    "next_hook_steps": [
        "Trace caller registers before entering decompression routine.",
        "Identify compressed source pointer for the early Other World dialogue package.",
        "Patch only the source dialogue package or add a branch guarded by LOG4_DEBUG_GATEWAY_UNLOCKED.",
        "Avoid patching the generic decompressor globally unless a safe branch condition is proven.",
    ],
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rom_sha1 = hashlib.sha1(ROM.read_bytes()).hexdigest() if ROM.exists() else "missing"
    data = {**FINDINGS, "base_rom_sha1": rom_sha1}
    manifest = OUT / "dialogue_trace_findings.json"
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Phase 39 — Dialogue trace package\n\n"
        "Runtime watchpoints showed that early dialogue text is written through IWRAM code rather than appearing as simple raw UTF-16 in ROM.\n\n"
        "## Key findings\n\n"
        "- EWRAM dialog region A: `0x0202DB00-0x0202E300`\n"
        "- EWRAM dialog region B: `0x0202C000-0x0202C200`\n"
        "- Main writer PC: `0x03000268`\n"
        "- Literal writer PC: `0x03000060`\n"
        "- ROM bytes for IWRAM routine around `0x03000268`: `0x007B7C0C`\n"
        "- ROM bytes for IWRAM routine around `0x03000060`: `0x007B7A04`\n\n"
        "## Interpretation\n\n"
        "The visible Bubbles/Gateway dialogue should be hooked by finding the compressed dialogue source/caller, not by blindly replacing NPC records.\n\n"
        f"Manifest: `{manifest.relative_to(ROOT)}`\n",
        encoding="utf-8",
    )
    print(f"Wrote {manifest.relative_to(ROOT)}")
    print(f"Wrote {DOC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
