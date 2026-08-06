# Phase 53 runtime report — native map lookup trace

Phase 53 instrumentation was run successfully in the headless GBA runtime.

## ROM

- `patch_output/DBZ_LOG4_phase53_native_map_findarea_trace.gba`
- SHA-1: `6c90b221878bef39ff125f9a07c685e1c1da8895`

## What was traced

The debug ROM hooks the native AreaEntry lookup function at `0x080089FC`. This function scans the Buu's Fury native map-entry table at `0x0808E2E0` and compares the requested `(r0, r1)` pair against each record's first two bytes.

The hook logs each lookup into EWRAM at `0x0203F800` without changing the lookup result.

## Runtime passes

- `playtest_output/phase53_trace_skip`: PASS after intro/menu skip flow.
- `playtest_output/phase53_trace_walk`: PASS after additional movement/dialogue flow.
- `playtest_output/phase53_trace_long`: PASS after longer story-progression input flow.

## Native lookup pairs observed

The long trace observed these AreaEntry requests:

| Index | r0 area | r1 room | Caller LR |
|---:|---:|---:|---:|
| 0 | `0x00` | `0x02` | `0x0800905B` |
| 1 | `0x00` | `0x04` | `0x0800905B` |
| 2 | `0x00` | `0x05` | `0x0800905B` |
| 3 | `0x00` | `0x06` | `0x0800905B` |
| 4 | `0x00` | `0x07` | `0x0800905B` |
| 5 | `0x00` | `0x01` | `0x0800905B` |
| 6 | `0x00` | `0x01` | `0x0800905B` |
| 7 | `0x00` | `0x62` | `0x0800905B` |
| 8 | `0x00` | `0x60` | `0x0800905B` |
| 9 | `0x00` | `0x02` | `0x0800905B` |
| 10 | `0x01` | `0x01` | `0x08008D71` |

## Engineering conclusion

This confirms the true native map-loading route is closer now:

1. Native maps are resolved by an `(area, room)` byte pair.
2. The primary native map-constructor region is around `0x08009030`, with the lookup return at `0x0800905B`.
3. Safe known pairs include `00:02`, `00:04`, `00:05`, `00:06`, `00:07`, `00:60`, `00:62`, and `01:01`.
4. The next step is to build a gated native warp that lets the Gateway enter the original engine initialization, then steer this constructor to a known safe pair before adding LOG1/LOG2/SUPER/GT/AF appended AreaEntry IDs.

## Honest status

- Runtime trace hook: **working**.
- Native map-loader entry points: **partially identified**.
- Gateway selection into true native maps: **not implemented yet**.
- Recommended playable ROM remains the Phase 51 / v0.3 warp-room build.
