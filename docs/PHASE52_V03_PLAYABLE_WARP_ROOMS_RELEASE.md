# Phase 52 — v0.3 Playable Warp Rooms Release

Packaged Phase 51 as the v0.3 debug release for tester handoff.

## Recommended file to test

`patch_output/LOG4_v0_3_playable_warp_rooms_pack.zip` → `roms/DBZ_LOG4_v0_3_PlayableWarpRooms.gba`

## Checksums

- ROM SHA-1: `f16c4b450afcab9205dd2410ee7e02ba11bab010`
- IPS SHA-1: `f242ab632affc7df36496a75888b4d53dc02002f`
- ZIP SHA-1: see `additive_content/release/v0_3_playable_warp_rooms_manifest.json` after package build.

## Runtime coverage

The package includes the Phase 51 runtime evidence when present. The headless test covers: Gateway boot, entering a room, moving the marker, L/R room cycling, pad warp, HOME return, and Start fallback into original Buu's Fury.

## Status

Playable debug warp layer: **yes**. Native Buu's Fury map loader warp: **not yet**. Base/original fallback: **yes**.
