#!/usr/bin/env python3
"""Phase 48: unified gateway test build.

Combines the most useful runtime-visible hooks into one tester ROM:
- LOG4 title/splash graphics runtime hook (kind-0 container).
- Bubbles/Gateway debug text labels from phase 26.
- Main dialogue text-bank hook from phase 45.
- Appended gateway/route payloads for future hooks.

This is the recommended single ROM for the next manual test cycle.
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
TITLE = ROOT / "additive_content" / "title_screen" / "LOG4_title_screen_240x160.png"
BG_PAL = ROOT / "tools" / "buusfury_disassembly" / "assets" / "palettes" / "bg.pal"
DRAGONBYTEZ = ROOT / "tools" / "DragonByteZ" / "dragonbytez-cli"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase48_unified_gateway_test"
MANIFEST = ROOT / "additive_content" / "phase48_unified_gateway" / "phase48_unified_gateway_manifest.json"
DOC = ROOT / "docs" / "PHASE48_UNIFIED_GATEWAY_TEST.md"
MAGIC = b"LOG4U48!"
VERSION = 1

# Title/splash hook.
OLD_SPLASH_VA = 0x083BE3D4
TITLE_POINTER_REFS = [0x00005414, 0x0001E744, 0x0001E9E0]

# Text bank hook.
TEXT_BANK_POINTER_OFFSET = 0x007B5B64
TEXT_BANK_ORIGINAL_VA = 0x0879BF2C
TEXT_BANK_ORIGINAL_OFFSET = 0x0079BF2C

TEXT_BANK_REPLACEMENTS = [
    ("Welcome to King Yemma's Castle. You're going to want to talk to King Yemma.", "Bubbles guards the Rift Gate. Choose Super, GT, AF, LOG1 or LOG2."),
    ("Sir, you can't go this way!", "Bubbles opens Rift Gate!"),
    ("Sir, you can't go this way! I'm afraid you're going to have to wait in line like...Wait a second!", "Bubbles: A rift is open. Super, GT, AF, LOG1 and LOG2 wait beyond Snake Way."),
    ("You still have your body!", "You can cross dimensions!"),
    ("Please, go ahead!", "Choose a rift!"),
]

@dataclass(frozen=True)
class TextPatch:
    offset: int
    old: str
    new: str
    note: str

DEBUG_TEXT_PATCHES = [
    TextPatch(0x5DBD0, "Snakeway", "Bubbles", "map/debug label"),
    TextPatch(0x5DE1C, "Other World Saga", "Bubbles Saga", "saga label"),
    TextPatch(0x5DF98, "Go to King Yemma's Castle", "Find Bubbles Gate", "first objective"),
    TextPatch(0x5DFCC, "Train with Other World Fighters", "Choose Bubbles Gate", "second objective"),
    TextPatch(0x6B57C, "Chapter 1", "Bubbles!", "chapter title"),
    TextPatch(0x6B590, "The Other World", "Bubbles Gateway", "chapter subtitle"),
    TextPatch(0x6513C, "King Yemma", "Bubbles", "NPC/database label"),
    TextPatch(0x65152, "King Yemma is a giant ogre who guards the entrance to the Other World.", "Bubbles guards the gate to Super, GT, AF, LOG1 and LOG2.", "database description"),
    TextPatch(0x651E0, "Yemma's Assistant", "Bubbles Guide", "NPC/database label"),
    TextPatch(0x65204, "This assistant helps King Yemma usher souls into the Other World.", "Talk to Bubbles on Snakeway to open Super, GT, AF, LOG1 and LOG2.", "NPC/database description"),
    TextPatch(0x64A44, "Bubbles is an ape who hangs out with King Kai.", "Bubbles helps open the Rift Gate.", "Bubbles database description"),
]

PAYLOAD_FILES = [
    ROOT / "additive_content" / "gateway" / "gateway_menu_layout.json",
    ROOT / "additive_content" / "gateway" / "gateway_state_machine.json",
    ROOT / "additive_content" / "gateway" / "gateway_menu_preview_240x160.png",
    ROOT / "additive_content" / "gateway" / "route_start_profiles.json",
    ROOT / "additive_content" / "phase31_gateway_interaction" / "gateway_interaction_contract.json",
    ROOT / "additive_content" / "phase32_first_route" / "log2_first_route_contract.json",
    ROOT / "additive_content" / "phase33_route_matrix" / "full_route_expansion_matrix.json",
    ROOT / "additive_content" / "phase36_save_flags" / "log4_save_flag_allocation.json",
]


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


def read_u32(data: bytes | bytearray, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def write_u32(data: bytearray, off: int, val: int) -> None:
    struct.pack_into("<I", data, off, val)


def align(v: int, b: int) -> int:
    return (v + b - 1) & ~(b - 1)


def header_checksum(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def utf16z(text: str) -> bytes:
    return text.encode("utf-16le") + b"\x00\x00"


def apply_debug_text(data: bytearray, patch: TextPatch) -> dict:
    old = utf16z(patch.old)
    if bytes(data[patch.offset:patch.offset + len(old)]) != old:
        raise SystemExit(f"Text precondition failed at 0x{patch.offset:06X}: {patch.old!r}")
    if len(patch.new) > len(patch.old):
        raise SystemExit(f"Text too long: {patch.new!r}")
    slot = bytearray(b"\x00" * len(old))
    nr = utf16z(patch.new)
    slot[:len(nr)] = nr
    data[patch.offset:patch.offset + len(slot)] = slot
    return {"offset": f"0x{patch.offset:06X}", "old": patch.old, "new": patch.new, "note": patch.note}


def load_bgr555_palette(path: Path) -> list[tuple[int, int, int]]:
    raw = path.read_bytes()
    out = []
    for i in range(0, 512, 2):
        v = raw[i] | (raw[i + 1] << 8)
        r = v & 31
        g = (v >> 5) & 31
        b = (v >> 10) & 31
        out.append(((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2)))
    return out


def nearest(px: tuple[int, int, int], pal: list[tuple[int, int, int]]) -> int:
    r, g, b = px
    best, bestd = 0, 10**12
    for i, (pr, pg, pb) in enumerate(pal):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < bestd:
            best, bestd = i, d
    return best


def title_indices() -> bytes:
    pal = load_bgr555_palette(BG_PAL)
    img = Image.open(TITLE).convert("RGB").resize((240, 160), Image.Resampling.NEAREST)
    return bytes(nearest(px, pal) for px in img.getdata())


def kind0_container(raw: bytes) -> bytes:
    return struct.pack("<II", 0, len(raw)) + raw


def append_container(data: bytearray, raw: bytes, alignment: int = 4) -> tuple[int, int]:
    off = align(len(data), alignment)
    data.extend(b"\xFF" * (off - len(data)))
    va = 0x08000000 + off
    data.extend(raw)
    return off, va


def decompress_text_bank() -> bytes:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "text.bin"
        subprocess.run([str(DRAGONBYTEZ), "decompress", str(BASE), hex(TEXT_BANK_ORIGINAL_OFFSET), "-o", str(out)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        return out.read_bytes()


def pad_text(new: str, old: str) -> str:
    if len(new) > len(old):
        raise ValueError(f"replacement too long: {new!r}")
    return new + (" " * (len(old) - len(new)))


def patch_text_bank(bank: bytes) -> tuple[bytes, list[dict]]:
    data = bytearray(bank)
    logs = []
    for old, new in TEXT_BANK_REPLACEMENTS:
        old_raw = old.encode("utf-16le")
        idx = data.find(old_raw)
        if idx < 0:
            raise SystemExit(f"Could not find {old!r} in text bank")
        new_raw = pad_text(new, old).encode("utf-16le")
        data[idx:idx + len(old_raw)] = new_raw
        logs.append({"offset_in_text_bank": f"0x{idx:04X}", "old": old, "new": new})
    return bytes(data), logs


def payload_zip() -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in PAYLOAD_FILES:
            if p.exists():
                zf.write(p, p.relative_to(ROOT).as_posix())
    return bio.getvalue()


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base SHA-1 mismatch")
    for ref in TITLE_POINTER_REFS:
        if read_u32(base, ref) != OLD_SPLASH_VA:
            raise SystemExit(f"Title pointer precondition failed at 0x{ref:06X}")
    if read_u32(base, TEXT_BANK_POINTER_OFFSET) != TEXT_BANK_ORIGINAL_VA:
        raise SystemExit("Text bank pointer precondition failed")
    data = bytearray(base)
    debug_text = [apply_debug_text(data, p) for p in DEBUG_TEXT_PATCHES]

    # Title screen hook.
    t_raw = title_indices()
    title_off, title_va = append_container(data, kind0_container(t_raw), 4)
    for ref in TITLE_POINTER_REFS:
        write_u32(data, ref, title_va)

    # Dialogue text bank hook.
    bank = decompress_text_bank()
    patched_bank, replacements = patch_text_bank(bank)
    text_off, text_va = append_container(data, kind0_container(patched_bank), 4)
    write_u32(data, TEXT_BANK_POINTER_OFFSET, text_va)

    # Data payload for gateway runtime contracts.
    payload = payload_zip()
    directory = json.dumps({"schema": "jurai.phase48.payload.v1", "files": [p.relative_to(ROOT).as_posix() for p in PAYLOAD_FILES if p.exists()], "payload_sha1": hashlib.sha1(payload).hexdigest()}, separators=(",", ":")).encode("utf-8")
    p_header = MAGIC + struct.pack("<III", VERSION, len(directory), len(payload))
    payload_off = len(data)
    data.extend(p_header + directory + payload)
    data[0xA0:0xAC] = b"LOG4UNIFIED" + b"\0"
    data[0xBD] = header_checksum(data)
    while len(data) % 4:
        data.append(0)
    final = bytes(data)

    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    manifest = {
        "schema": "jurai.phase48.unified_gateway_test.v1",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "title_hook": {"new_va": f"0x{title_va:08X}", "offset": f"0x{title_off:06X}", "pointer_refs": [f"0x{x:06X}" for x in TITLE_POINTER_REFS]},
        "text_bank_hook": {"new_va": f"0x{text_va:08X}", "offset": f"0x{text_off:06X}", "pointer_offset": f"0x{TEXT_BANK_POINTER_OFFSET:06X}", "replacements": replacements},
        "debug_text_patches": debug_text,
        "payload_offset": f"0x{payload_off:06X}",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Phase 48 — Unified gateway test ROM\n\n"
        "Combines title runtime hook, Bubbles debug text, dialogue text-bank hook and gateway route payloads into one tester ROM.\n\n"
        f"Output ROM: `{gba.relative_to(ROOT)}`\n\n"
        f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n\n"
        f"Manifest: `{MANIFEST.relative_to(ROOT)}`\n",
        encoding="utf-8",
    )
    txt.write_text(DOC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {gba}")


if __name__ == "__main__":
    main()
