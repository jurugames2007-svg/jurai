#!/usr/bin/env python3
"""Phase 46: runtime title-screen graphics hook.

This is the first real graphics hook for the LOG4 title screen. It does not
replace the original splash block. Instead it:
- converts LOG4 title art to the native 240x160 8bpp splash format using the
  existing Buu's Fury BG palette;
- appends a Webfoot/JCALG-compatible type-1 raw-literal container;
- redirects the three known splash-image pointer literals from 0x083BE3D4 to
  the appended container.

The original splash data remains in the ROM as fallback.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
TITLE = ROOT / "additive_content" / "title_screen" / "LOG4_title_screen_240x160.png"
BG_PAL = ROOT / "tools" / "buusfury_disassembly" / "assets" / "palettes" / "bg.pal"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase46_title_screen_runtime_hook"
MANIFEST = ROOT / "additive_content" / "title_screen" / "phase46_title_screen_runtime_hook_manifest.json"
DOC = ROOT / "docs" / "PHASE46_TITLE_SCREEN_RUNTIME_HOOK.md"
DRAGONBYTEZ = ROOT / "tools" / "DragonByteZ" / "dragonbytez-cli"
OLD_SPLASH_VA = 0x083BE3D4
POINTER_REFS = [0x00005414, 0x0001E744, 0x0001E9E0]
WIDTH, HEIGHT = 240, 160
DECLARED_SIZE = WIDTH * HEIGHT


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


def load_bgr555_palette(path: Path) -> list[tuple[int, int, int]]:
    raw = path.read_bytes()
    colors = []
    for i in range(0, min(len(raw), 512), 2):
        val = raw[i] | (raw[i + 1] << 8)
        r = val & 0x1F
        g = (val >> 5) & 0x1F
        b = (val >> 10) & 0x1F
        colors.append(((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2)))
    colors += [(0, 0, 0)] * (256 - len(colors))
    return colors[:256]


def nearest(color: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> int:
    r, g, b = color
    best = 0
    best_d = 1 << 60
    for i, (pr, pg, pb) in enumerate(palette):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_d:
            best = i
            best_d = d
    return best


def convert_title_to_indices() -> bytes:
    if not TITLE.exists():
        raise SystemExit(f"Missing title art: {TITLE}")
    pal = load_bgr555_palette(BG_PAL)
    img = Image.open(TITLE).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.NEAREST)
    return bytes(nearest(px, pal) for px in img.getdata())


class BitWriter:
    def __init__(self) -> None:
        self.bits: list[int] = []

    def bit(self, v: int) -> None:
        self.bits.append(1 if v else 0)

    def bits_value(self, value: int, count: int) -> None:
        for shift in range(count - 1, -1, -1):
            self.bit((value >> shift) & 1)

    def bytes(self) -> bytes:
        out = bytearray()
        for i in range(0, len(self.bits), 32):
            word_bits = self.bits[i:i + 32]
            while len(word_bits) < 32:
                word_bits.append(0)
            word = 0
            for bit in word_bits:
                word = (word << 1) | bit
            out.extend(struct.pack("<I", word))
        return bytes(out)


def encode_raw_literal_container(raw: bytes) -> bytes:
    if len(raw) != DECLARED_SIZE:
        raise ValueError(len(raw))
    bw = BitWriter()
    # Control path in DragonByteZ/Webfoot decoder:
    # not literal (0), not normal phrase (0), one-byte/raw branch (1),
    # get(4)==0 => oneBytePhraseValue=-1, next bit 1 => raw byte-pair run.
    bw.bit(0)
    bw.bit(0)
    bw.bit(1)
    bw.bits_value(0, 4)
    bw.bit(1)
    for i in range(0, len(raw), 2):
        bw.bits_value(raw[i], 8)
        bw.bits_value(raw[i + 1], 8)
        if i + 2 < len(raw):
            bw.bit(1)
    payload = bw.bytes()
    return struct.pack("<II", 1, len(raw)) + payload


def verify_container(container: bytes, expected: bytes) -> None:
    with tempfile.TemporaryDirectory() as td:
        temp_rom = Path(td) / "temp.gba"
        # Place the container at 0 for DragonByteZ decompression.
        temp_rom.write_bytes(container + b"\x00" * 16)
        out = Path(td) / "out.bin"
        subprocess.run([str(DRAGONBYTEZ), "decompress", str(temp_rom), "0x0", "-o", str(out)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        got = out.read_bytes()
        if got != expected:
            raise SystemExit(f"container self-test failed: {len(got)} bytes")


def header_checksum(data: bytearray) -> int:
    return (-0x19 - sum(data[0xA0:0xBD])) & 0xFF


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base SHA-1 mismatch")
    for ref in POINTER_REFS:
        if read_u32(base, ref) != OLD_SPLASH_VA:
            raise SystemExit(f"Splash pointer precondition failed at 0x{ref:06X}")
    raw = convert_title_to_indices()
    container = encode_raw_literal_container(raw)
    verify_container(container, raw)
    modified = bytearray(base)
    off = align(len(modified), 4)
    modified.extend(b"\xFF" * (off - len(modified)))
    va = 0x08000000 + off
    modified.extend(container)
    for ref in POINTER_REFS:
        write_u32(modified, ref, va)
    modified[0xA0:0xAC] = b"LOG4TITLE46\0"  # 12 bytes
    modified[0xBD] = header_checksum(modified)
    while len(modified) % 4:
        modified.append(0)
    final = bytes(modified)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    manifest = {
        "schema": "jurai.phase46.title_screen_runtime_hook.v1",
        "policy": "append_new_splash_container_and_redirect_known_title_pointers",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "old_splash_va": f"0x{OLD_SPLASH_VA:08X}",
        "new_splash_va": f"0x{va:08X}",
        "container_offset": f"0x{off:06X}",
        "container_size": len(container),
        "pointer_refs": [f"0x{x:06X}" for x in POINTER_REFS],
        "raw_index_sha1": hashlib.sha1(raw).hexdigest(),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Phase 46 — Title screen runtime hook\n\n"
        "Appended a new 240×160 splash/title graphics container and redirected the three known original title/splash pointers to it.\n\n"
        f"Output ROM: `{gba.relative_to(ROOT)}`\n\n"
        f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n\n"
        f"New splash VA: `0x{va:08X}`\n\n"
        f"Manifest: `{MANIFEST.relative_to(ROOT)}`\n\n"
        "Runtime title-screen QA is required to confirm where in the title flow this splash appears.\n",
        encoding="utf-8",
    )
    txt.write_text(DOC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {gba}")
    print(f"Container size {len(container)} bytes at 0x{off:06X}")


if __name__ == "__main__":
    main()
