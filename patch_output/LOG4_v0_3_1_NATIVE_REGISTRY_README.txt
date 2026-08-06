Dragon Ball: The Legacy of Goku 4 — v0.3.1 Native Registry Debug Pack
=====================================================================

Recommended advanced test ROM:
  roms/DBZ_LOG4_v0_3_1_NativeRegistry.gba

ROM SHA-1: c2e76758af2cd989485e1b74de668c295cb88101
IPS SHA-1: c929846e68d867df943ae94208a48a245e946f6c

What works:
- Same playable boot Gateway warp-room layer as v0.3.
- ORIGINAL/Start fallback still boots the untouched Buu's Fury flow.
- Native AreaEntry table is extended additively from 452 to 457 entries.
- Route IDs F0:01..F0:05 are registered for SUPER/GT/AF/LOG1/LOG2.

Honest limitation:
- Gateway selections still enter debug rooms. They do not yet call the native map constructor.
- This pack is the bridge toward true native map warps, not the final native warp implementation.
