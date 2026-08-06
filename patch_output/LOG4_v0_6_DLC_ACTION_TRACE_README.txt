Dragon Ball: The Legacy of Goku 4 — v0.6 DLC Action + Native Trace Hooks
=====================================================================

Recommended test ROM:
  roms/DBZ_LOG4_v0_6_DLCActionNativeTrace.gba

ROM SHA-1: c68113e8a2b097e0f549b56216cd796410ffb73b
IPS SHA-1: 2bad0a47830b3e8252da3c0acbdc44f6ef437b64

What works:
- v0.5 dynamic DLC assets remain hooked.
- SELECT cycles the 3-frame 32x32 hero/enemy sheets at runtime.
- Native AreaEntry status widget and EWRAM state are visible/testable.
- Native AreaEntry lookup trace hook is installed at 0x080089FC for original fallback research.

Honest limitation:
- Native AreaEntry lookup is traced, but the Gateway is not yet handed to the native map constructor.
