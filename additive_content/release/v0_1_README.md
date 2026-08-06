# Dragon Ball: The Legacy of Goku 4 — v0.1 Bubbles Gateway Test Pack

## Recommended test ROM

Open this first in mGBA:

```text
roms/DBZ_LOG4_v0_1_DEBUG_BubblesGateway.gba
```

Expected visible debug text:

- `Bubbles!`
- `Bubbles Gateway`
- `Find Bubbles Gate`
- `Choose Bubbles Gate`

## Canon/original-first ROM

Use this to confirm the original early game remains intact:

```text
roms/DBZ_LOG4_v0_1_CANON_OriginalFirst.gba
```

## Experimental NPC probe

If you want to search Snakeway/Riftway for an injected NPC candidate:

```text
roms/experimental/DBZ_LOG4_phase24_multi_gatekeeper_probe.gba
```

This may not visibly show anything yet; it is an experimental native NPC-record probe.

## Current limitation

The Gateway is visible as text/debug data. A fully interactable Bubbles menu still requires decoding the native NPC/script trigger format.
