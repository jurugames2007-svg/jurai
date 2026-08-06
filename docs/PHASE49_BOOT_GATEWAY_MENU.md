# Phase 49 — Boot Gateway Menu

Created a real boot-time Gateway selector hook before Buu's Fury starts.

Output ROM: `patch_output/DBZ_LOG4_phase49_boot_gateway_menu.gba`

Modified SHA-1: `05823a9e846a14777121e9bee5254c0e1731f401`

## Controls

- Up/Down: select route.
- A/Start on Original: boot Buu's Fury.
- A/Start on Super/GT/AF/LOG1/LOG2: show route/dimension debug screen.
- B: return to menu.
- Start on route/dimension screen: boot Buu's Fury.

This is the first true start-of-game warp selector. It is currently a route/debug screen selector; actual native map warps are the next hook.
