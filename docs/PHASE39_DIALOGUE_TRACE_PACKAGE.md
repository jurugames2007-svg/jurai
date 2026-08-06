# Phase 39 — Dialogue trace package

Runtime watchpoints showed that early dialogue text is written through IWRAM code rather than appearing as simple raw UTF-16 in ROM.

## Key findings

- EWRAM dialog region A: `0x0202DB00-0x0202E300`
- EWRAM dialog region B: `0x0202C000-0x0202C200`
- Main writer PC: `0x03000268`
- Literal writer PC: `0x03000060`
- ROM bytes for IWRAM routine around `0x03000268`: `0x007B7C0C`
- ROM bytes for IWRAM routine around `0x03000060`: `0x007B7A04`

## Interpretation

The visible Bubbles/Gateway dialogue should be hooked by finding the compressed dialogue source/caller, not by blindly replacing NPC records.

Manifest: `additive_content/phase39_dialogue_trace/dialogue_trace_findings.json`
