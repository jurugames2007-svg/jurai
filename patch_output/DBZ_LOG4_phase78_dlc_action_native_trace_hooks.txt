# Phase 78 — DLC action/native-trace hooks ROM

Built the v0.6 hook ROM with action-frame asset hooks and a native AreaEntry lookup trace hook.

- Output ROM: `patch_output/DBZ_LOG4_phase78_dlc_action_native_trace_hooks.gba`
- SHA-1: `c68113e8a2b097e0f549b56216cd796410ffb73b`
- ARM Gateway hook VA: `0x0894F44C`
- Native lookup trace hook VA: `0x08A1DF54`
- Route state EWRAM: `0x0203F700`
- Native lookup trace EWRAM: `0x0203F740`

SELECT in a route room cycles the 3-frame DLC sprite/enemy sheets. Original fallback remains available.

Honest limitation: native AreaEntry lookups are traced, but the Gateway still does not hand custom routes to the native map constructor.
