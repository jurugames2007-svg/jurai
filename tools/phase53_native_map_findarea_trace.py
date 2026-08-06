#!/usr/bin/env python3
"""Phase 53: instrument the native AreaEntry lookup for map-warp research.

The boot Gateway is playable now, but true native map warps require knowing what
area IDs the Buu's Fury engine asks for during startup/new-game/map loads.  This
research ROM hooks the native function at 0x080089FC (the function that scans the
AreaEntry table at 0x0808E2E0) and logs each (area, room) lookup into EWRAM.

This is a trace-only debug ROM, not the recommended player build.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase53_native_map_findarea_trace"
DOC = ROOT / "docs" / "PHASE53_NATIVE_MAP_FINDAREA_TRACE.md"
MANIFEST = ROOT / "additive_content" / "phase53_native_map_trace" / "phase53_native_map_findarea_trace_manifest.json"

HOOK_OFF = 0x000089FC
HOOK_VA = 0x080089FC
RETURN_VA = 0x08008A08
COUNT_FUNC_THUMB = 0x080125E1
LOG_BASE = 0x0203F800
MAX_LOGS = 64

try:
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
except Exception as exc:  # pragma: no cover
    raise SystemExit("Missing keystone-engine. Install with: .venv/bin/python -m pip install keystone-engine") from exc

ASM = r"""
    .thumb
_start:
    @ Log native AreaEntry lookup arguments r0/r1 while preserving the
    @ function's original callee-saved behaviour.
    push {r2, r3}
    ldr r2, =LOG_BASE
    ldrb r3, [r2, #1]
    cmp r3, #0x53
    beq magic_ok
    movs r3, #0
    strb r3, [r2]
    movs r3, #0x53
    strb r3, [r2, #1]
magic_ok:
    ldrb r3, [r2]
    cmp r3, #MAX_LOGS
    bhs log_done
    adds r3, #1
    strb r3, [r2]
    subs r3, #1
    lsls r3, r3, #3
    adds r2, #0x10
    adds r2, r2, r3
    strb r0, [r2]
    strb r1, [r2, #1]
    mov r3, lr
    str r3, [r2, #4]
log_done:
    pop {r2, r3}

    @ Original overwritten function prologue and native count call.
    push {r3-r5, lr}
    adds r4, r0, #0
    adds r5, r1, #0
    ldr r3, =COUNT_FUNC_THUMB
    ldr r2, =after_count + 1
    mov lr, r2
    bx r3
after_count:
    movs r2, #0
    ldr r3, =RETURN_THUMB
    bx r3
"""


def assemble(appended_va: int) -> bytes:
    src = (
        ASM.replace("LOG_BASE", f"0x{LOG_BASE:08X}")
        .replace("MAX_LOGS", str(MAX_LOGS))
        .replace("COUNT_FUNC_THUMB", f"0x{COUNT_FUNC_THUMB:08X}")
        .replace("RETURN_THUMB", f"0x{RETURN_VA | 1:08X}")
    )
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    enc, _ = ks.asm(src, addr=appended_va)
    return bytes(enc)


def hchk(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def ips_patch(original: bytes, modified: bytes) -> bytes:
    out = bytearray(b"PATCH")
    pos = 0
    while pos < len(modified):
        if pos < len(original) and original[pos] == modified[pos]:
            pos += 1
            continue
        start = pos
        pos += 1
        while pos < len(modified) and pos - start < 0xFFFF:
            if pos < len(original) and original[pos] == modified[pos]:
                break
            pos += 1
        chunk = modified[start:pos]
        out.extend(start.to_bytes(3, "big"))
        out.extend(len(chunk).to_bytes(2, "big"))
        out.extend(chunk)
    out.extend(b"EOF")
    out.extend(len(modified).to_bytes(3, "big"))
    return bytes(out)


def main() -> int:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base ROM SHA-1 mismatch")
    data = bytearray(base)
    original = bytes(data[HOOK_OFF:HOOK_OFF + 12])
    expected = bytes.fromhex("38 B5 04 1C 0D 1C 09 F0 ED FD 00 22")
    if original != expected:
        raise SystemExit(f"Unexpected hook bytes at 0x{HOOK_OFF:06X}: {original.hex(' ')}")

    appended_off = (len(data) + 3) & ~3
    appended_va = 0x08000000 + appended_off
    code = assemble(appended_va)
    data.extend(b"\xFF" * (appended_off - len(data)))
    data.extend(code)

    # Absolute Thumb jump at 0x080089FC:
    #   ldr r2, [pc, #4]   ; literal at 0x08008A04
    #   bx r2
    #   nop
    #   nop
    #   .word appended|1
    patch = struct.pack("<HHHHI", 0x4A01, 0x4710, 0x46C0, 0x46C0, appended_va | 1)
    data[HOOK_OFF:HOOK_OFF + len(patch)] = patch
    data[0xA0:0xAC] = b"LOG4TRACE53\0"
    data[0xBD] = hchk(data)
    while len(data) % 4:
        data.append(0)
    final = bytes(data)

    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))

    manifest = {
        "schema": "jurai.phase53.native_map_findarea_trace.v1",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "hook_function": "AreaEntry lookup / native map table scan",
        "hook_va": f"0x{HOOK_VA:08X}",
        "return_va": f"0x{RETURN_VA:08X}",
        "appended_code_va": f"0x{appended_va:08X}",
        "appended_code_size": len(code),
        "log_base": f"0x{LOG_BASE:08X}",
        "max_logs": MAX_LOGS,
        "log_format": {
            "base+0": "count",
            "base+1": "magic 0x53",
            "base+0x10+n*8+0": "r0 area/group byte",
            "base+0x10+n*8+1": "r1 room/subarea byte",
            "base+0x10+n*8+4": "caller LR/return address"
        },
        "original_overwritten_bytes": original.hex(" "),
        "recommended_use": "Run original intro/new-game flow, snapshot EWRAM 0x0203F800..0x0203FA20, decode route IDs for native warp hook research.",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    doc = (
        "# Phase 53 — Native map AreaEntry lookup trace\n\n"
        "Phase 53 adds a trace-only hook to the native AreaEntry lookup at `0x080089FC`. The function compares `(r0, r1)` against the native map table at `0x0808E2E0`, so tracing it tells us which area IDs the engine requests during boot/new-game/map transitions.\n\n"
        f"- Output ROM: `{gba.relative_to(ROOT)}`\n"
        f"- Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n"
        f"- Hook VA: `0x{HOOK_VA:08X}`\n"
        f"- Appended Thumb code VA: `0x{appended_va:08X}`\n"
        f"- EWRAM log base: `0x{LOG_BASE:08X}`\n\n"
        "## Log format\n\n"
        "- `0x0203F800`: count\n"
        "- `0x0203F801`: magic `0x53`\n"
        "- Each 8-byte entry starts at `0x0203F810`:\n"
        "  - `+0`: lookup `r0` area/group byte\n"
        "  - `+1`: lookup `r1` room/subarea byte\n"
        "  - `+4`: caller LR/return address\n\n"
        "This ROM is for research only, not the recommended user test build. It supports the next milestone: replacing debug rooms with true native map-loader warps.\n"
    )
    DOC.write_text(doc, encoding="utf-8")
    txt.write_text(doc, encoding="utf-8")
    print(f"Wrote {gba.relative_to(ROOT)}")
    print(f"SHA-1 {hashlib.sha1(final).hexdigest()}")
    print(f"Trace log base 0x{LOG_BASE:08X}, code size {len(code)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
