# Phase 49 — Boot Gateway runtime report

## Build

```text
patch_output/DBZ_LOG4_phase49_boot_gateway_menu.gba
```

SHA-1:

```text
05823a9e846a14777121e9bee5254c0e1731f401
```

## Result

Automated headless runtime test completed:

```text
PASS_RUNTIME_SCRIPT_COMPLETED
```

Evidence:

```text
playtest_output/phase49_boot_gateway_contact.png
playtest_output/phase49_menu_controls_contact.png
playtest_output/phase49_menu_controls/gateway-controls-result.json
```

## What works

- A boot-time Gateway selector appears before the original game.
- Up/Down changes the selected option.
- A/Start on `ORIGINAL` boots the original Buu's Fury flow.
- A/Start on Super/GT/AF/LOG1/LOG2 shows route/dimension debug screens.
- B returns from route/dimension screen to the Gateway selector.
- Start from a route/dimension screen boots original Buu's Fury.

## Limitation

This is currently a debug selector with route info screens, not native map warps yet. The next hook is actual map transition for the selected route/dimension.
