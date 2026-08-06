Dragon Ball: The Legacy of Goku 4 — v0.5 DLC Runtime Hooks
==========================================================

Recommended test ROM:
  roms/DBZ_LOG4_v0_5_DLCRuntimeHooks.gba

ROM SHA-1: 8ddc84c0a95a1316441a4066da8a2024afe7cdf5
IPS SHA-1: 4d63974ded0ee7c957ef338268edf89266095fbc

What works now:
- Boot Gateway rooms are playable.
- Route rooms dynamically draw 32x32 playable/enemy sprites from the LOG4A32 bank.
- Route rooms dynamically draw portraits/icons from the LOG4A32 bank.
- Route room render scans the native AreaEntry table for F0:01..F0:05 and logs the pointer in EWRAM.
- START/ORIG still boots original Buu's Fury.

Honest limitation:
- This still does not hand control to a native Buu's Fury map. It proves the runtime asset hooks and native lookup bridge before the constructor hook.
