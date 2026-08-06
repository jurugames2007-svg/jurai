Dragon Ball: The Legacy of Goku 4 — v0.3 Playable Warp Rooms
==============================================================

Recommended test ROM:
  roms/DBZ_LOG4_v0_3_PlayableWarpRooms.gba

ROM SHA-1: f16c4b450afcab9205dd2410ee7e02ba11bab010
IPS SHA-1: f242ab632affc7df36496a75888b4d53dc02002f

What works in this debug build:
- Boot-time Gateway selector appears immediately.
- ORIGINAL boots the untouched Buu's Fury entry point.
- SUPER / GT / AF / LOG1 DIM / LOG2 DIM open playable route rooms.
- D-pad moves a tester marker inside each room.
- A on HOME returns to Gateway.
- A on NEXT warps to the next dimension room.
- L/R cycles route rooms.
- A on ORIG, or Start in any room, boots original Buu's Fury.

Honest limitation:
This is a real runtime/playable appended hook, but route rooms are still a safe debug layer.
They do not yet call Buu's Fury native map transition code. Native map warps are the next target.
