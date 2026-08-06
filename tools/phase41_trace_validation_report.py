#!/usr/bin/env python3
"""Phase 41: validate trace scripts and summarize available dialogue hook evidence."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "additive_content" / "phase41_trace_validation"
DOC = ROOT / "docs" / "PHASE41_TRACE_VALIDATION_REPORT.md"
SCRIPT_FILES = [
    ROOT / "tools" / "gba_headless" / "watch_dialog_writes.mjs",
    ROOT / "tools" / "gba_headless" / "watch_long_dialog_writes.mjs",
    ROOT / "tools" / "gba_headless" / "disasm_iwram.mjs",
    ROOT / "tools" / "gba_headless" / "snapshot_iwram.mjs",
]
EVIDENCE_SUMMARY = {
    "ewram_dialog_buffer_region_a": "0x0202DB00-0x0202E300",
    "ewram_dialog_buffer_region_b": "0x0202C000-0x0202C200",
    "writer_iwram_pc_main": "0x03000268",
    "writer_iwram_pc_literal": "0x03000060",
    "rom_source_for_iwram_03000268_exact32": "0x007B7C0C",
    "rom_source_for_iwram_03000060_exact32": "0x007B7A04",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [{"path": p.relative_to(ROOT).as_posix(), "exists": p.exists(), "size": p.stat().st_size if p.exists() else 0} for p in SCRIPT_FILES]
    result = {"schema": "jurai.phase41.trace_validation.v2", "scripts": rows, "scripts_complete": all(r["exists"] for r in rows), "evidence_summary": EVIDENCE_SUMMARY, "note": "Raw playtest_output traces are ignored by git; this report stores the reproducible scripts and distilled findings."}
    out = OUT / "trace_validation_report.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Phase 41 — Trace validation\n\n"
        f"Trace scripts complete: {result['scripts_complete']}\n\n"
        "Raw playtest outputs are intentionally not committed, but the distilled findings are preserved here and in Phase 39.\n\n"
        "## Distilled evidence\n\n"
        + "\n".join(f"- {k}: `{v}`" for k, v in EVIDENCE_SUMMARY.items())
        + f"\n\nReport: `{out.relative_to(ROOT)}`\n",
        encoding="utf-8",
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
