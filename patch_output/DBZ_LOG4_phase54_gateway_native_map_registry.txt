# Phase 54 — Gateway native map registry

Phase 54 keeps the playable Phase 51 boot Gateway/warp rooms and additionally registers five additive native AreaEntry stubs for future real map-loader warps.

- Output ROM: `patch_output/DBZ_LOG4_phase54_gateway_native_map_registry.gba`
- Modified SHA-1: `c2e76758af2cd989485e1b74de668c295cb88101`
- Extended AreaEntry table VA: `0x088CE730`
- Native AreaEntry count: `452 -> 457`

## Registered native IDs

| Route | New pair | Cloned safe pair | Original clone index |
|---|---:|---:|---:|
| SUPER | `F0:01` | `00:02` | 1 |
| GT | `F0:02` | `00:04` | 3 |
| AF | `F0:03` | `00:05` | 4 |
| LOG1_DIM | `F0:04` | `00:60` | 29 |
| LOG2_DIM | `F0:05` | `00:62` | 31 |

## What this means

The engine's native AreaEntry lookup can now resolve route-specific IDs (`F0:01` through `F0:05`) if a future hook asks for them. This is the registry step needed before making the boot Gateway call or steer the native map constructor.

## What is still pending

Gateway selections still open the Phase 51 debug rooms, not native Buu's Fury maps. The next hook must enter original engine initialization and then invoke/steer the native map constructor around `0x08009030` using either a known safe original pair or one of these appended `F0:*` route IDs.

## Safety

Original AreaEntry records are copied unchanged before the new stubs. Existing lookups still find the original entries first. Original fallback remains available from the Gateway via Start/ORIG.
