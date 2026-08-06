# Project completion checklist

## Current milestone

**v0.1 Bubbles Gateway Debug** is ready for user testing.

Recommended ROM:

```text
patch_output/DBZ_LOG4_phase26_bubbles_start_gateway.gba
```

Release/test package:

```text
patch_output/LOG4_v0_1_bubbles_gateway_test_pack.zip
```

## What is ready

- Buu's Fury base ROM identity verified.
- Original-first postgame gateway line defined.
- Super / GT / AF routes defined as post-Kid-Buu expansion targets.
- LOG1 / LOG2 defined as pre-Kid-Buu dimensions.
- Bubbles Gateway debug text visible at the beginning.
- Runtime smoke tests pass for current debug ROMs.
- Snakeway/Riftway NPC probe variants exist for manual testing.

## What remains before a true playable expansion

1. Decode native NPC/script trigger format.
2. Make Bubbles or Gate Guide a real interactable NPC.
3. Show real gateway menu in-game.
4. Wire menu options to route/dimension debug starts.
5. Create first real map transition for LOG1/LOG2 dimensions.
6. Add reviewed sprites, portraits, icons and maps to native banks.
7. Implement route-specific enemies and objectives.
8. Implement save/flag mapping safely.
9. Full mGBA and hardware-like QA.

## Definition of done for next milestone v0.2

- Talking to Bubbles opens at least a text menu or dialogue choice.
- One selectable option changes game state or warps to a safe existing map.
- No crash in mGBA/headless runtime.
- Original Buu's Fury route remains available as fallback.
