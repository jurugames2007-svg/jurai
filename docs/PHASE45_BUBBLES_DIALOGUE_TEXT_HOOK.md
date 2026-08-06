# Phase 45 — Bubbles dialogue text hook

Decompressed the main text bank, replaced early King Yemma/Snakeway assistant dialogue with equal-length Bubbles Gateway text, appended it as an uncompressed Webfoot container, and redirected the text bank pointer.

Output ROM: `patch_output/DBZ_LOG4_phase45_bubbles_dialogue_text_hook.gba`
Modified SHA-1: `7d6416c4934904c7ff318685df0cb6e381c91e20`
New text bank VA: `0x08800000`
Manifest: `additive_content/phase45_dialogue_text_hook/phase45_bubbles_dialogue_text_hook_manifest.json`

## Replacements

- `Welcome to King Yemma's Castle. You're going to want to talk to King Yemma.` -> `Bubbles guards the Rift Gate. Choose Super, GT, AF, LOG1 or LOG2.` at 0x8F5A
- `Sir, you can't go this way!` -> `Bubbles opens Rift Gate!` at 0x917E
- `Sir, you can't go this way! I'm afraid you're going to have to wait in line like...Wait a second!` -> `Bubbles: A rift is open. Super, GT, AF, LOG1 and LOG2 wait beyond Snake Way.` at 0x91B4
- `You still have your body!` -> `You can cross dimensions!` at 0x9278
- `Please, go ahead!` -> `Choose a rift!` at 0x9362
