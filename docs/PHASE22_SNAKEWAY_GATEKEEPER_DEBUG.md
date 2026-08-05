# Phase 22 — Snakeway Gateway NPC debug

Creates a debug-visible Rift Gate Guide concept for Snakeway/Riftway.
Native NPC/entity hook is still pending, but text/contract/payload are now ready.

Output ROM: `patch_output/DBZ_LOG4_phase22_snakeway_gatekeeper_debug.gba`
Modified SHA-1: `a31822d40ea31b94a2af9085216f975504be8735`

## Text patches

- 0x05DBD0: `Snakeway` -> `Riftway` (map name debug)
- 0x05DE1C: `Other World Saga` -> `Rift Gate Saga` (saga label debug)
- 0x05DF98: `Go to King Yemma's Castle` -> `Find Rift Gate Guide` (objective debug)
- 0x05DFCC: `Train with Other World Fighters` -> `Choose Gateway Dimension` (objective debug)
- 0x06B57C: `Chapter 1` -> `Rift Gate` (chapter title debug)
- 0x06B590: `The Other World` -> `Snakeway Gate` (chapter subtitle debug)
- 0x06513C: `King Yemma` -> `Gate Guide` (encyclopedia/NPC label debug)
- 0x0651E0: `Yemma's Assistant` -> `Rift Gate Guide` (NPC label debug)
- 0x065204: `This assistant helps King Yemma usher souls into the Other World.` -> `Guide at Snakeway opens Super, GT, AF, LOG1 and LOG2.` (NPC description debug)
