# Phase 41 — Trace validation

Trace scripts complete: True

Raw playtest outputs are intentionally not committed, but the distilled findings are preserved here and in Phase 39.

## Distilled evidence

- ewram_dialog_buffer_region_a: `0x0202DB00-0x0202E300`
- ewram_dialog_buffer_region_b: `0x0202C000-0x0202C200`
- writer_iwram_pc_main: `0x03000268`
- writer_iwram_pc_literal: `0x03000060`
- rom_source_for_iwram_03000268_exact32: `0x007B7C0C`
- rom_source_for_iwram_03000060_exact32: `0x007B7A04`

Report: `additive_content/phase41_trace_validation/trace_validation_report.json`
