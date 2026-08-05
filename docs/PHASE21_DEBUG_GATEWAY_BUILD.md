# Phase 21.1 — Debug gateway build

Optional debug build for quickly seeing gateway labels from the start.
This is not the canonical original-first story ROM.

Output ROM: `patch_output/DBZ_LOG4_phase21_debug_gateway_build.gba`
Modified SHA-1: `b1710d97a8325441b1d89c4ab66fd00a028896a1`

## Text patches

- 0x0579E4: `Select Game` -> `Rift Gate` (save/select screen label)
- 0x0579FC: `New Game` -> `Gateway` (new game label in debug build)
- 0x058168: `No Saved Games` -> `Route Select` (no save label)
- 0x06B57C: `Chapter 1` -> `RIFT GATE` (chapter overlay debug)
- 0x06B708: `Chapter 10` -> `RIFT GATE` (chapter overlay debug duplicate)
- 0x06B72C: `Chapter 11` -> `RIFT GATE` (chapter overlay debug duplicate)
- 0x06B752: `Chapter 12` -> `RIFT GATE` (chapter overlay debug duplicate)
- 0x06B590: `The Other World` -> `Post Kid Buu` (chapter subtitle debug)
- 0x05DC32: `The Other World` -> `Rift Gateway` (map/name debug)
