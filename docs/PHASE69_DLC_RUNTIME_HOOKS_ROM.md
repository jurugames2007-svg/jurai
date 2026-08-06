# Phase 69 — DLC runtime hooks ROM

Built the runtime-hook ROM that keeps the boot Gateway playable while dynamically blitting DLC assets from the Phase 61 `LOG4A32` bank.

- Output ROM: `patch_output/DBZ_LOG4_phase69_dlc_runtime_hooks.gba`
- SHA-1: `8ddc84c0a95a1316441a4066da8a2024afe7cdf5`
- Appended ARM hook VA: `0x0894F44C`
- Image base VA: `0x0894FA20`
- EWRAM route-state base: `0x0203F700`

Runtime hooks applied: sprite/enemy blit, portrait/icon blit, native AreaEntry table bridge, EWRAM route-state logging.

Honest limitation: still a Gateway/debug-layer hook; native map constructor handoff remains pending.
