# Phase 53 — Native map AreaEntry lookup trace

Phase 53 adds a trace-only hook to the native AreaEntry lookup at `0x080089FC`. The function compares `(r0, r1)` against the native map table at `0x0808E2E0`, so tracing it tells us which area IDs the engine requests during boot/new-game/map transitions.

- Output ROM: `patch_output/DBZ_LOG4_phase53_native_map_findarea_trace.gba`
- Modified SHA-1: `6c90b221878bef39ff125f9a07c685e1c1da8895`
- Hook VA: `0x080089FC`
- Appended Thumb code VA: `0x08800000`
- EWRAM log base: `0x0203F800`

## Log format

- `0x0203F800`: count
- `0x0203F801`: magic `0x53`
- Each 8-byte entry starts at `0x0203F810`:
  - `+0`: lookup `r0` area/group byte
  - `+1`: lookup `r1` room/subarea byte
  - `+4`: caller LR/return address

This ROM is for research only, not the recommended user test build. It supports the next milestone: replacing debug rooms with true native map-loader warps.

## Runtime result

Headless runtime validation passed. The trace observed native lookup pairs including `00:02`, `00:04`, `00:05`, `00:06`, `00:07`, `00:60`, `00:62`, and `01:01`. The primary native map-constructor callsite returns through `0x0800905B`, placing the next hook target around `0x08009030`.

See `docs/PHASE53_RUNTIME_NATIVE_MAP_TRACE.md` and `additive_content/phase53_native_map_trace/phase53_runtime_trace_report.json`.
