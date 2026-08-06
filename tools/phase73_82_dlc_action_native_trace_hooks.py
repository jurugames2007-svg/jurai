#!/usr/bin/env python3
"""Phases 73-82: DLC action hooks + native AreaEntry lookup trace.

This is the next 10-phase hook block after v0.5:

- Adds interactive action-frame hooks to the DLC Gateway rooms. SELECT cycles
  through the 3-frame 32x32 sheets already stored in the LOG4A32 asset bank.
- Adds a native AreaEntry status widget and keeps route state in EWRAM.
- Adds a safe trace hook to Buu's Fury's native AreaEntry lookup at 0x080089FC.
  It logs native map lookup arguments during original fallback flow.

Honest scope: these are runtime hooks and safe native lookup trace hooks. The
Gateway still does not drive the native map constructor directly.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM, KS_MODE_THUMB

import phase63_72_dlc_runtime_hooks as prev
from phase51_boot_gateway_warp_rooms import branch_opcode, hchk, ips_patch

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
PHASE61_ROM = ROOT / "patch_output" / "DBZ_LOG4_phase61_dlc_asset_bank_payload.gba"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase78_dlc_action_native_trace_hooks"
PACK_ZIP = ROOT / "patch_output" / "LOG4_v0_6_dlc_action_native_trace_hooks_pack.zip"
STATE_BASE = prev.STATE_BASE
TRACE_BASE = 0x0203F740
CONSTRUCTOR_HOOK_OFF = 0x000089FC
CONSTRUCTOR_HOOK_VA = 0x080089FC
CONSTRUCTOR_RETURN_THUMB = 0x08008A09
COUNT_FUNC_THUMB = 0x080125E1
SCREEN_BYTES = 240 * 160 * 2
FIXED_ZIP_TIME = (2026, 8, 5, 12, 0, 0)

PHASE_DIRS = {
    73: ROOT / "additive_content" / "phase73_dlc_action_frame_hook",
    74: ROOT / "additive_content" / "phase74_native_status_widget_hook",
    75: ROOT / "additive_content" / "phase75_native_lookup_trace_hook",
    76: ROOT / "additive_content" / "phase76_route_action_state_hook",
    77: ROOT / "additive_content" / "phase77_v06_room_interaction_contract",
    78: ROOT / "additive_content" / "phase78_dlc_action_native_trace_rom",
    79: ROOT / "additive_content" / "phase79_dlc_action_runtime_validation",
    80: ROOT / "additive_content" / "phase80_native_lookup_trace_runtime_validation",
    81: ROOT / "additive_content" / "phase81_v06_action_trace_pack",
    82: ROOT / "additive_content" / "phase82_v06_hook_doctor",
}
DOCS = ROOT / "docs"

BASE_ASM = prev.ASM_TEMPLATE


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def action_asm_template() -> str:
    asm = BASE_ASM
    asm = asm.replace(
        "    tst r0, #0x08\n    bne jump_original\n    tst r0, #0x100",
        "    tst r0, #0x08\n    bne jump_original\n    tst r0, #0x04   @ SELECT cycles DLC action frame\n    bne toggle_action\n    tst r0, #0x100",
    )
    asm = asm.replace(
        "    mov r6, #120\n    mov r7, #110\n    bl render_room",
        "    mov r6, #120\n    mov r7, #110\n    bl reset_action_state\n    bl render_room",
    )
    asm = asm.replace(
        "prev_room:\n    cmp r4, #1",
        "toggle_action:\n    ldr r0, =STATE_BASE\n    ldr r1, [r0, #16]\n    cmp r1, #2\n    moveq r1, #0\n    addne r1, r1, #1\n    str r1, [r0, #16]\n    bl render_room\n    b release_and_loop\n\nprev_room:\n    cmp r4, #1",
    )
    asm = asm.replace(
        "    bl native_lookup_route\n    bl blit_route_assets\n    bl draw_player",
        "    bl native_lookup_route\n    bl blit_route_assets\n    bl draw_native_status_widget\n    bl draw_player",
    )
    asm = asm.replace(
        "render_room:\n    stmdb sp!, {lr}",
        "reset_action_state:\n    stmdb sp!, {r0-r1, lr}\n    ldr r0, =STATE_BASE\n    mov r1, #0\n    str r1, [r0, #16]\n    ldmia sp!, {r0-r1, pc}\n\nrender_room:\n    stmdb sp!, {lr}",
    )
    asm = asm.replace(
        "blit_playable:\n    stmdb sp!, {lr}\n    mov r1, #96",
        "blit_playable:\n    stmdb sp!, {r10-r12, lr}\n    ldr r10, =STATE_BASE\n    ldr r10, [r10, #16]\n    lsl r10, r10, #6\n    add r0, r0, r10\n    mov r1, #96",
    )
    asm = asm.replace("    bl blit_asset_skip_zero\n    ldmia sp!, {pc}\nblit_enemy:", "    bl blit_asset_skip_zero\n    ldmia sp!, {r10-r12, pc}\nblit_enemy:", 1)
    asm = asm.replace(
        "blit_enemy:\n    stmdb sp!, {lr}\n    mov r1, #96",
        "blit_enemy:\n    stmdb sp!, {r10-r12, lr}\n    ldr r10, =STATE_BASE\n    ldr r10, [r10, #16]\n    lsl r10, r10, #6\n    add r0, r0, r10\n    mov r1, #96",
    )
    asm = asm.replace("    bl blit_asset_skip_zero\n    ldmia sp!, {pc}\nblit_portrait:", "    bl blit_asset_skip_zero\n    ldmia sp!, {r10-r12, pc}\nblit_portrait:", 1)
    marker = "draw_player:\n"
    widget = r"""
draw_native_status_widget:
    stmdb sp!, {r4-r8, lr}
    ldr r0, =STATE_BASE
    ldr r1, [r0, #12]
    cmp r1, #0
    ldreq r4, =0x001F      @ red if native lookup failed
    ldrne r4, =0x03E0      @ green if F0 native AreaEntry resolved
    ldr r0, =0x0600DE7C    @ x=158 y=118
    mov r5, #6
nsw_row:
    mov r8, r0
    mov r2, #16
nsw_col:
    strh r4, [r8], #2
    subs r2, r2, #1
    bne nsw_col
    add r0, r0, #480
    subs r5, r5, #1
    bne nsw_row
    @ action-frame pips at x=106/114/122, y=122
    ldr r0, =STATE_BASE
    ldr r1, [r0, #16]
    ldr r0, =0x0600E548    @ x=106 y=122
    mov r5, #0
nsw_pip_loop:
    cmp r5, r1
    ldreq r4, =0x03FF
    ldrne r4, =0x4210
    mov r6, #4
    mov r8, r0
nsw_pip_row:
    mov r2, #4
    mov r7, r8
nsw_pip_col:
    strh r4, [r7], #2
    subs r2, r2, #1
    bne nsw_pip_col
    add r8, r8, #480
    subs r6, r6, #1
    bne nsw_pip_row
    add r0, r0, #16
    add r5, r5, #1
    cmp r5, #3
    blt nsw_pip_loop
    ldmia sp!, {r4-r8, pc}

"""
    asm = asm.replace(marker, widget + marker)
    return asm


ASM_V06 = action_asm_template()


def assemble_arm(appended_va: int, image_base: int, constants: dict[str, int]) -> bytes:
    text = ASM_V06
    replacements = {
        "STATE_BASE": f"0x{STATE_BASE:08X}",
        "NATIVE_LOOKUP_THUMB": f"0x{prev.NATIVE_LOOKUP_THUMB:08X}",
        "MAP_TABLE_VA": f"0x{prev.current_map_table_va():08X}",
        "MAP_ENTRY_COUNT": str(prev.MAP_ENTRY_COUNT),
        "IMAGE_BASE": f"0x{image_base:08X}",
    }
    for k, v in constants.items():
        replacements[k] = f"0x{v:08X}"
    for k in sorted(replacements, key=len, reverse=True):
        text = text.replace(k, replacements[k])
    ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
    enc, _ = ks.asm(text, addr=appended_va)
    return bytes(enc)


CONSTRUCTOR_TRACE_ASM = r"""
    .thumb
_start:
    @ Safe native AreaEntry lookup trace hook. This is the same low-risk target
    @ proven in Phase 53, now integrated into the v0.6 action build.
    push {r2, r3}
    ldr r2, =TRACE_BASE
    ldrb r3, [r2, #1]
    cmp r3, #0x82
    beq magic_ok
    movs r3, #0
    strb r3, [r2]
    movs r3, #0x82
    strb r3, [r2, #1]
magic_ok:
    ldrb r3, [r2]
    cmp r3, #0x20
    bhs log_done
    adds r3, #1
    strb r3, [r2]
    subs r3, #1
    lsls r3, r3, #5
    adds r2, #0x20
    adds r2, r2, r3
    strb r0, [r2]
    strb r1, [r2, #1]
    mov r3, lr
    str r3, [r2, #4]
log_done:
    pop {r2, r3}

    @ Original overwritten AreaEntry lookup prologue and native count call.
    push {r3-r5, lr}
    adds r4, r0, #0
    adds r5, r1, #0
    ldr r3, =COUNT_FUNC_THUMB
    ldr r2, =after_count + 1
    mov lr, r2
    bx r3
after_count:
    movs r2, #0
    ldr r3, =CONSTRUCTOR_RETURN_THUMB
    bx r3
"""

def assemble_constructor_trace(appended_va: int) -> bytes:
    src = (CONSTRUCTOR_TRACE_ASM.replace("TRACE_BASE", f"0x{TRACE_BASE:08X}")
           .replace("CONSTRUCTOR_RETURN_THUMB", f"0x{CONSTRUCTOR_RETURN_THUMB:08X}")
           .replace("COUNT_FUNC_THUMB", f"0x{COUNT_FUNC_THUMB:08X}"))
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    enc, _ = ks.asm(src, addr=appended_va)
    return bytes(enc)


def patch_constructor_trace(data: bytearray) -> dict:
    original = bytes(data[CONSTRUCTOR_HOOK_OFF:CONSTRUCTOR_HOOK_OFF + 12])
    expected = bytes.fromhex("38 b5 04 1c 0d 1c 09 f0 ed fd 00 22")
    if original != expected:
        raise SystemExit(f"Unexpected native lookup bytes: {original.hex(' ')}")
    appended_off = (len(data) + 3) & ~3
    data.extend(b"\xFF" * (appended_off - len(data)))
    appended_va = 0x08000000 + appended_off
    code = assemble_constructor_trace(appended_va)
    data.extend(code)
    patch = struct.pack("<HHHHI", 0x4A01, 0x4710, 0x46C0, 0x46C0, appended_va | 1)
    data[CONSTRUCTOR_HOOK_OFF:CONSTRUCTOR_HOOK_OFF + len(patch)] = patch
    return {
        "native_lookup_trace_hook_va": f"0x{CONSTRUCTOR_HOOK_VA:08X}",
        "native_lookup_trace_va": f"0x{appended_va:08X}",
        "native_lookup_trace_size": len(code),
        "trace_base": f"0x{TRACE_BASE:08X}",
        "overwritten_bytes": original.hex(" "),
    }


def build_rom(constants: dict[str, int]) -> dict:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base ROM SHA-1 mismatch")
    source = bytearray(PHASE61_ROM.read_bytes())
    images = prev.build_images()
    appended_off = (len(source) + 3) & ~3
    appended_va = 0x08000000 + appended_off
    provisional = assemble_arm(appended_va, appended_va, constants)
    image_base = appended_va + len(provisional)
    code = assemble_arm(appended_va, image_base, constants)
    image_base = appended_va + len(code)
    code = assemble_arm(appended_va, image_base, constants)
    image_base = appended_va + len(code)
    source.extend(b"\xFF" * (appended_off - len(source)))
    source.extend(code)
    source.extend(images)
    constructor = patch_constructor_trace(source)
    struct.pack_into("<I", source, 0, branch_opcode(0x08000000, appended_va))
    source[0xA0:0xAC] = b"LOG4HOOK78\0\0"
    source[0xBD] = hchk(source)
    while len(source) % 4:
        source.append(0)
    final = bytes(source)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    doc = (
        "# Phase 78 — DLC action/native-trace hooks ROM\n\n"
        "Built the v0.6 hook ROM with action-frame asset hooks and a native AreaEntry lookup trace hook.\n\n"
        f"- Output ROM: `{gba.relative_to(ROOT)}`\n"
        f"- SHA-1: `{sha1_bytes(final)}`\n"
        f"- ARM Gateway hook VA: `0x{appended_va:08X}`\n"
        f"- Native lookup trace hook VA: `{constructor['native_lookup_trace_va']}`\n"
        f"- Route state EWRAM: `0x{STATE_BASE:08X}`\n"
        f"- Native lookup trace EWRAM: `0x{TRACE_BASE:08X}`\n\n"
        "SELECT in a route room cycles the 3-frame DLC sprite/enemy sheets. Original fallback remains available.\n\n"
        "Honest limitation: native AreaEntry lookups are traced, but the Gateway still does not hand custom routes to the native map constructor.\n"
    )
    DOCS.joinpath("PHASE78_DLC_ACTION_NATIVE_TRACE_ROM.md").write_text(doc, encoding="utf-8")
    txt.write_text(doc, encoding="utf-8")
    return {
        "schema": "jurai.phase78.dlc_action_native_trace_rom.v1",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": sha1_bytes(final),
        "source_phase61_rom": PHASE61_ROM.relative_to(ROOT).as_posix(),
        "gateway_hook_va": f"0x{appended_va:08X}",
        "gateway_hook_size": len(code),
        "image_base_va": f"0x{image_base:08X}",
        "state_base": f"0x{STATE_BASE:08X}",
        "action_state_offset": "+0x10",
        **constructor,
        "hooks": ["SELECT action frame hook", "native status widget", "route action EWRAM state", "native lookup trace", "original fallback preserved"],
        "native_map_constructor_handoff": False,
    }


def write_phase_manifests(binding_manifest: dict, rom_manifest: dict) -> None:
    for d in PHASE_DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
    p73 = {
        "schema": "jurai.phase73.dlc_action_frame_hook.v1",
        "rom": rom_manifest["output_gba"],
        "input": "SELECT in route room",
        "state_address": f"0x{STATE_BASE + 0x10:08X}",
        "frames": [0, 1, 2],
        "effect": "Playable/enemy blit source is offset by frame*64 bytes inside each 96x32 sheet.",
    }
    PHASE_DIRS[73].joinpath("phase73_dlc_action_frame_hook_manifest.json").write_text(json.dumps(p73, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE73_DLC_ACTION_FRAME_HOOK.md").write_text("# Phase 73 — DLC action-frame hook\n\nApplied SELECT-driven 3-frame animation/action selection for 32×32 DLC sprites and enemies.\n", encoding="utf-8")
    p74 = {"schema": "jurai.phase74.native_status_widget_hook.v1", "rom": rom_manifest["output_gba"], "state_pointer_address": f"0x{STATE_BASE + 0x0C:08X}", "visual": "green/red native AreaEntry status marker plus action-frame pips", "status": "Applied in route-room render."}
    PHASE_DIRS[74].joinpath("phase74_native_status_widget_hook_manifest.json").write_text(json.dumps(p74, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE74_NATIVE_STATUS_WIDGET_HOOK.md").write_text("# Phase 74 — Native status widget hook\n\nApplied visual native lookup status marker and action pips to DLC route rooms.\n", encoding="utf-8")
    p75 = {"schema": "jurai.phase75.native_lookup_trace_hook.v1", "rom": rom_manifest["output_gba"], "hook_va": f"0x{CONSTRUCTOR_HOOK_VA:08X}", "trace_base": f"0x{TRACE_BASE:08X}", "record_size": 32, "max_records": 32, "status": "Applied to native AreaEntry lookup; active after original fallback boots."}
    PHASE_DIRS[75].joinpath("phase75_native_lookup_trace_hook_manifest.json").write_text(json.dumps(p75, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE75_NATIVE_LOOKUP_TRACE_HOOK.md").write_text("# Phase 75 — Native lookup trace hook\n\nApplied a Thumb trace hook at native AreaEntry lookup `0x080089FC`, logging native lookup args to EWRAM `0x0203F740`.\n", encoding="utf-8")
    p76 = {"schema": "jurai.phase76.route_action_state_hook.v1", "rom": rom_manifest["output_gba"], "state_layout": {"0x0203F700": "L4HK magic", "0x0203F704": "route", "0x0203F708": "F0 pair", "0x0203F70C": "AreaEntry pointer", "0x0203F710": "action frame"}, "status": "Applied."}
    PHASE_DIRS[76].joinpath("phase76_route_action_state_hook_manifest.json").write_text(json.dumps(p76, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE76_ROUTE_ACTION_STATE_HOOK.md").write_text("# Phase 76 — Route/action state hook\n\nExtended EWRAM route state with the current DLC action frame.\n", encoding="utf-8")
    p77 = {"schema": "jurai.phase77.v06_room_interaction_contract.v1", "controls": ["D-pad move", "SELECT action frame", "A on HOME/NEXT/ORIG pads", "B menu", "START original"], "status": "Runtime contract for v0.6 hook ROM."}
    PHASE_DIRS[77].joinpath("phase77_v06_room_interaction_contract.json").write_text(json.dumps(p77, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE77_V06_ROOM_INTERACTION_CONTRACT.md").write_text("# Phase 77 — v0.6 room interaction contract\n\nDocumented controls for the new action-frame runtime hook.\n", encoding="utf-8")
    PHASE_DIRS[78].joinpath("phase78_dlc_action_native_trace_rom_manifest.json").write_text(json.dumps(rom_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_runtime_script() -> Path:
    script = ROOT / "tools" / "gba_headless" / "test_phase78_dlc_action_hooks.mjs"
    script.write_text(f"""import {{ HeadlessRuntime }} from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
const romPath = process.argv[2];
const out = process.argv[3] ?? 'playtest_output/phase78_dlc_action_hooks';
await fs.mkdir(out, {{ recursive: true }});
const runtime = await HeadlessRuntime.create({{ romPath, outputDir: out, logFn: () => {{}} }});
const STATE = 0x{STATE_BASE:08X};
const tap = async (button, times = 1) => {{ for (let i=0; i<times; i++) {{ await press(button, {{hold:4}}); await wait({{frames:8}}); }} }};
const script = `
 const STATE = ${{STATE}};
 const tap = ${{tap.toString()}};
 await wait({{frames:60}});
 await tap('down', 1); await tap('a', 1); await wait({{frames:20}});
 await takeScreenshot({{name:'00_super_frame0'}});
 if (read32(STATE) !== 0x4B48344C || read32(STATE+4) !== 1 || read32(STATE+8) !== 0xF001 || read32(STATE+12) === 0 || read32(STATE+16) !== 0) throw new Error('frame0 state failed');
 await tap('select', 1); await wait({{frames:20}}); await takeScreenshot({{name:'01_super_frame1'}});
 if (read32(STATE+16) !== 1) throw new Error('frame1 action failed');
 await tap('select', 1); await wait({{frames:20}}); await takeScreenshot({{name:'02_super_frame2'}});
 if (read32(STATE+16) !== 2) throw new Error('frame2 action failed');
 await tap('select', 1); await wait({{frames:20}}); await takeScreenshot({{name:'03_super_frame0_again'}});
 if (read32(STATE+16) !== 0) throw new Error('frame reset action failed');
 await tap('r', 4); await wait({{frames:20}}); await takeScreenshot({{name:'04_log2_frame0'}});
 if (read32(STATE+4) !== 5 || read32(STATE+8) !== 0xF005 || read32(STATE+12) === 0 || read32(STATE+16) !== 0) throw new Error('LOG2 state failed');
 await takeMemorySnapshot({{name:'phase78-route-state', address: STATE, length: 32}});
 await tap('start', 1); await wait({{frames:240}}); await takeScreenshot({{name:'05_original_fallback_after_start'}});
 await takeMemorySnapshot({{name:'phase78-native-lookup-trace', address: 0x{TRACE_BASE:08X}, length: 0x120}});
`;
let status='PASS', error=null;
try {{ await runtime.executeScript(script); await runtime.writeFinalSaveState(); }} catch(e) {{ status='FAIL'; error=String(e.stack||e); }}
await fs.writeFile(`${{out}}/phase78-dlc-action-hooks-result.json`, JSON.stringify({{status,error}}, null, 2));
if(status==='FAIL') {{ console.error(error); process.exit(1); }}
console.log('PASS_PHASE78_DLC_ACTION_HOOKS');
""", encoding="utf-8")
    return script


def write_validation_reports(status: str = "NOT_RUN", lookup_status: str = "NOT_RUN") -> None:
    report79 = {"schema": "jurai.phase79.dlc_action_runtime_validation.v1", "rom": OUT_PREFIX.with_suffix(".gba").relative_to(ROOT).as_posix(), "rom_sha1": sha1(OUT_PREFIX.with_suffix(".gba")), "runtime_status": status, "output_dir": "playtest_output/phase78_dlc_action_hooks", "coverage": ["SELECT frame cycling", "dynamic asset frame offsets", "native status pointer still resolves", "LOG2 route state", "original fallback"]}
    PHASE_DIRS[79].mkdir(parents=True, exist_ok=True)
    PHASE_DIRS[79].joinpath("phase79_dlc_action_runtime_validation_report.json").write_text(json.dumps(report79, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE79_DLC_ACTION_RUNTIME_VALIDATION.md").write_text(f"# Phase 79 — DLC action runtime validation\n\nStatus: `{status}`\n", encoding="utf-8")
    report80 = {"schema": "jurai.phase80.native_lookup_trace_runtime_validation.v1", "rom": OUT_PREFIX.with_suffix(".gba").relative_to(ROOT).as_posix(), "runtime_status": lookup_status, "trace_base": f"0x{TRACE_BASE:08X}", "evidence": "playtest_output/phase78_dlc_action_hooks/memory-phase78-native-lookup-trace.json", "honest_note": "Trace hook is installed. It logs when original flow reaches native AreaEntry lookup calls in the automated window."}
    PHASE_DIRS[80].mkdir(parents=True, exist_ok=True)
    PHASE_DIRS[80].joinpath("phase80_native_lookup_trace_runtime_validation_report.json").write_text(json.dumps(report80, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE80_NATIVE_LOOKUP_TRACE_RUNTIME_VALIDATION.md").write_text(f"# Phase 80 — Native lookup trace runtime validation\n\nStatus: `{lookup_status}`\n", encoding="utf-8")


def package(status: str = "NOT_RUN") -> dict:
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    readme = ROOT / "patch_output" / "LOG4_v0_6_DLC_ACTION_TRACE_README.txt"
    readme.write_text(
        "Dragon Ball: The Legacy of Goku 4 — v0.6 DLC Action + Native Trace Hooks\n"
        "=====================================================================\n\n"
        "Recommended test ROM:\n"
        "  roms/DBZ_LOG4_v0_6_DLCActionNativeTrace.gba\n\n"
        f"ROM SHA-1: {sha1(gba)}\n"
        f"IPS SHA-1: {sha1(ips)}\n\n"
        "What works:\n"
        "- v0.5 dynamic DLC assets remain hooked.\n"
        "- SELECT cycles the 3-frame 32x32 hero/enemy sheets at runtime.\n"
        "- Native AreaEntry status widget and EWRAM state are visible/testable.\n"
        "- Native AreaEntry lookup trace hook is installed at 0x080089FC for original fallback research.\n\n"
        "Honest limitation:\n"
        "- Native AreaEntry lookup is traced, but the Gateway is not yet handed to the native map constructor.\n",
        encoding="utf-8",
    )
    entries: list[tuple[Path, str]] = [(gba, "roms/DBZ_LOG4_v0_6_DLCActionNativeTrace.gba"), (ips, "patches/DBZ_LOG4_v0_6_DLCActionNativeTrace.ips"), (readme, "README.txt")]
    manifest_files = [
        (73, "phase73_dlc_action_frame_hook_manifest.json"), (74, "phase74_native_status_widget_hook_manifest.json"), (75, "phase75_native_lookup_trace_hook_manifest.json"),
        (76, "phase76_route_action_state_hook_manifest.json"), (77, "phase77_v06_room_interaction_contract.json"), (78, "phase78_dlc_action_native_trace_rom_manifest.json"),
        (79, "phase79_dlc_action_runtime_validation_report.json"), (80, "phase80_native_lookup_trace_runtime_validation_report.json"),
    ]
    for ph, name in manifest_files:
        p = PHASE_DIRS[ph] / name
        if p.exists(): entries.append((p, f"manifests/{name}"))
    for doc in [
        "PHASE73_DLC_ACTION_FRAME_HOOK.md", "PHASE74_NATIVE_STATUS_WIDGET_HOOK.md", "PHASE75_NATIVE_LOOKUP_TRACE_HOOK.md", "PHASE76_ROUTE_ACTION_STATE_HOOK.md",
        "PHASE77_V06_ROOM_INTERACTION_CONTRACT.md", "PHASE78_DLC_ACTION_NATIVE_TRACE_ROM.md", "PHASE79_DLC_ACTION_RUNTIME_VALIDATION.md", "PHASE80_NATIVE_LOOKUP_TRACE_RUNTIME_VALIDATION.md",
        "PHASE81_V06_ACTION_TRACE_PACK.md", "PHASE82_V06_HOOK_DOCTOR.md",
    ]:
        p = DOCS / doc
        if p.exists(): entries.append((p, f"docs/{doc}"))
    for extra in [PHASE_DIRS[80] / "phase80_native_lookup_trace_decoded.json"]:
        if extra.exists(): entries.append((extra, "manifests/" + extra.name))
    for ev in [
        ROOT / "playtest_output" / "phase78_dlc_action_hooks" / "phase78-dlc-action-hooks-result.json",
        ROOT / "playtest_output" / "phase78_dlc_action_hooks" / "memory-phase78-route-state.json",
        ROOT / "playtest_output" / "phase78_dlc_action_hooks" / "memory-phase78-native-lookup-trace.json",
        ROOT / "playtest_output" / "phase78_dlc_action_hooks" / "screenshot-00_super_frame0.png",
        ROOT / "playtest_output" / "phase78_dlc_action_hooks" / "screenshot-01_super_frame1.png",
        ROOT / "playtest_output" / "phase78_dlc_action_hooks" / "screenshot-02_super_frame2.png",
        ROOT / "playtest_output" / "phase78_dlc_action_hooks" / "screenshot-04_log2_frame0.png",
        ROOT / "playtest_output" / "phase78_dlc_action_hooks" / "screenshot-05_original_fallback_after_start.png",
        ROOT / "playtest_output" / "phase78_native_lookup_trace_skip" / "skip-playtest-result.json",
        ROOT / "playtest_output" / "phase78_native_lookup_trace_skip" / "screenshot-final.png",
    ]:
        if ev.exists(): entries.append((ev, "runtime_evidence/" + ev.name))
    tmp = PACK_ZIP.with_suffix(".zip.tmp")
    if tmp.exists(): tmp.unlink()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in sorted(entries, key=lambda x: x[1]):
            info = zipfile.ZipInfo(arc, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, src.read_bytes())
    if PACK_ZIP.exists(): PACK_ZIP.unlink()
    tmp.rename(PACK_ZIP)
    manifest = {"schema": "jurai.phase81.v06_action_trace_pack.v1", "package": PACK_ZIP.relative_to(ROOT).as_posix(), "package_sha1": sha1(PACK_ZIP), "recommended_rom_in_zip": "roms/DBZ_LOG4_v0_6_DLCActionNativeTrace.gba", "rom_sha1": sha1(gba), "ips_sha1": sha1(ips), "runtime_status": status, "phase_block": list(range(73, 83)), "action_frame_hooks": True, "native_lookup_trace_hook": True, "native_map_constructor_handoff": False}
    PHASE_DIRS[81].mkdir(parents=True, exist_ok=True)
    PHASE_DIRS[81].joinpath("phase81_v06_action_trace_pack_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE81_V06_ACTION_TRACE_PACK.md").write_text(f"# Phase 81 — v0.6 action/trace pack\n\nPackage: `{PACK_ZIP.relative_to(ROOT)}`\n\nRuntime status: `{status}`\n", encoding="utf-8")
    return manifest


def write_phase82(status: str = "NOT_RUN") -> None:
    PHASE_DIRS[82].mkdir(parents=True, exist_ok=True)
    note = {"schema": "jurai.phase82.v06_hook_doctor.v1", "latest_rom": OUT_PREFIX.with_suffix(".gba").relative_to(ROOT).as_posix(), "latest_package": PACK_ZIP.relative_to(ROOT).as_posix(), "runtime_status": status, "doctor_expected_update": "project_doctor includes phase78 ROM and v0.6 package."}
    PHASE_DIRS[82].joinpath("phase82_v06_hook_doctor_note.json").write_text(json.dumps(note, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOCS.joinpath("PHASE82_V06_HOOK_DOCTOR.md").write_text("# Phase 82 — v0.6 hook doctor\n\nPrepared doctor metadata for the v0.6 action/native-trace hook block.\n", encoding="utf-8")


def main() -> int:
    prev.ensure_phase61()
    binding_manifest, constants = prev.route_bindings()
    rom_manifest = build_rom(constants)
    write_phase_manifests(binding_manifest, rom_manifest)
    write_runtime_script()
    write_validation_reports("NOT_RUN", "NOT_RUN")
    package("NOT_RUN")
    write_phase82("NOT_RUN")
    print(f"Wrote {OUT_PREFIX.with_suffix('.gba').relative_to(ROOT)}")
    print(f"ROM SHA-1 {sha1(OUT_PREFIX.with_suffix('.gba'))}")
    print(f"Wrote {PACK_ZIP.relative_to(ROOT)}")
    print(f"ZIP SHA-1 {sha1(PACK_ZIP)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
