# Phase 46 — Title screen runtime hook

Appended a new 240×160 splash/title graphics container and redirected the three known original title/splash pointers to it.

Output ROM: `patch_output/DBZ_LOG4_phase46_title_screen_runtime_hook.gba`

Modified SHA-1: `90b56a0ba388d2975012b53ce424996d2a70fcbc`

New splash VA: `0x08800000`

Manifest: `additive_content/title_screen/phase46_title_screen_runtime_hook_manifest.json`

Runtime title-screen QA is required to confirm where in the title flow this splash appears.
