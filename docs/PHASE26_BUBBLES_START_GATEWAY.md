# Phase 26 — Bubbles Start Gateway

Safe debug build that makes Bubbles the visible gateway guide at the start of the game.
Native NPC interaction bytecode is still pending, but this build is deterministic and easy to test.

Output ROM: `patch_output/DBZ_LOG4_phase26_bubbles_start_gateway.gba`
Modified SHA-1: `3aa4a54f95dd218f7494ea54def741883a6a8c7e`

## Patches

- 0x05DBD0: `Snakeway` -> `Bubbles` (start map/debug label)
- 0x05DE1C: `Other World Saga` -> `Bubbles Saga` (saga label)
- 0x05DF98: `Go to King Yemma's Castle` -> `Find Bubbles Gate` (first objective)
- 0x05DFCC: `Train with Other World Fighters` -> `Choose Bubbles Gate` (second objective)
- 0x06B57C: `Chapter 1` -> `Bubbles!` (chapter title)
- 0x06B590: `The Other World` -> `Bubbles Gateway` (chapter subtitle)
- 0x06513C: `King Yemma` -> `Bubbles` (NPC/database label)
- 0x065152: `King Yemma is a giant ogre who guards the entrance to the Other World.` -> `Bubbles guards the gate to Super, GT, AF, LOG1 and LOG2.` (database description)
- 0x0651E0: `Yemma's Assistant` -> `Bubbles Guide` (NPC/database label)
- 0x065204: `This assistant helps King Yemma usher souls into the Other World.` -> `Talk to Bubbles on Snakeway to open Super, GT, AF, LOG1 and LOG2.` (NPC/database description)
- 0x064A44: `Bubbles is an ape who hangs out with King Kai.` -> `Bubbles helps open the Rift Gate.` (Bubbles database description)
