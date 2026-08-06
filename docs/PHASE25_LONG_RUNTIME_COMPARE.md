# Phase 25 long runtime comparison

Automated long input sequence was run against the original ROM and all six Snakeway NPC variants.

## Result

All variants completed the runtime script without emulator exceptions.

However, captured screenshots for the tested route were pixel-identical to the original baseline:

```text
v01_template65_line: total changed pixels = 0
v02_template65_actor297_u16_06: total changed pixels = 0
v03_template141_line: total changed pixels = 0
v04_template146_cluster: total changed pixels = 0
v05_template156_actor297_u16_06: total changed pixels = 0
v06_template65_actor297_u16_0a: total changed pixels = 0
```

Comparison CSV:

```text
playtest_output/phase25_long_variant_compare.csv
```

## Interpretation

The variants do not crash, but they also do not visibly affect the automated early route. This likely means one or more of the following:

1. The tested route does not reach the exact Snakeway map segment where the NPC array would be evaluated.
2. The map entry being modified is not the runtime map entry for the visible Snakeway gameplay segment.
3. `npcs_pointer` is not sufficient; NPCs may be spawned by scripts/triggers instead.
4. The copied `0x20` records need additional fields or script registration to render.

## Recommendation

Route A by blind NPC-record variants is currently low-yield. The next step should focus on decoding the existing interaction that shows the early Other World dialogue, then reuse that script/trigger as the gateway entry point.
