# Phase 55 — v0.3.1 Native Registry Release

Phase 55 packages the Phase 54 advanced debug build. It keeps the playable v0.3 boot warp rooms and adds the first additive native map registry for route IDs.

## Recommended advanced ROM

`patch_output/LOG4_v0_3_1_native_registry_pack.zip` → `roms/DBZ_LOG4_v0_3_1_NativeRegistry.gba`

## Checksums

- ROM SHA-1: `c2e76758af2cd989485e1b74de668c295cb88101`
- IPS SHA-1: `c929846e68d867df943ae94208a48a245e946f6c`
- Base playable v0.3/Phase51 SHA-1: `f16c4b450afcab9205dd2410ee7e02ba11bab010`

## Status

- Playable Gateway rooms: **yes**.
- Original game fallback: **yes**.
- Native map IDs registered additively: **yes**.
- Gateway-to-native-map warp: **not yet**.

## Why this matters

Phase 53 proved the native AreaEntry lookup path. Phase 54 registers route-specific native IDs (`F0:01` through `F0:05`) without replacing original entries. The next step is to steer the constructor around `0x08009030` from the Gateway into one of these IDs or a known safe original map pair.
