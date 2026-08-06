# Phase 51 — Boot Gateway Playable Warp Rooms

Phase 51 upgrades the Phase 49 boot Gateway from static route info screens into a playable, self-contained warp-point layer.

- Output ROM: `patch_output/DBZ_LOG4_phase51_boot_gateway_warp_rooms.gba`
- IPS patch: `patch_output/DBZ_LOG4_phase51_boot_gateway_warp_rooms.ips`
- Modified SHA-1: `f16c4b450afcab9205dd2410ee7e02ba11bab010`
- Header title: `LOG4WARP51`
- Appended ARM code VA: `0x08800000`
- Image base VA: `0x08800330`

## What is playable now

- Start the ROM and the Gateway selector appears immediately.
- Choose `SUPER`, `GT`, `AF`, `LOG1 DIM`, or `LOG2 DIM` with A.
- Each route opens a route-specific 240x160 GBA Mode 3 room.
- D-pad moves the yellow/white tester marker.
- A on `HOME` returns to the Gateway menu.
- A on `NEXT` warps to the next dimension room.
- A on `ORIG`, or Start anywhere in a room, boots the untouched original Buu's Fury entry point.
- L/R cycles previous/next dimension room for fast testing.
- B returns to the Gateway menu.

## Honest limitation

This is a real runtime/playable hook, but it is still a debug warp-room layer drawn by our appended ARM code. It does **not yet** invoke the native Buu's Fury map loader or place the player on original engine maps. That is the next engineering target.

## Safety

The build remains additive: it appends code and screen data after the base ROM, branches at boot, and preserves `Start`/`ORIG` as a fallback into the original `0x080000C0` Buu's Fury entry. No original maps, flags, or save structures are overwritten by this phase.
