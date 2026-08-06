#!/usr/bin/env python3
"""Phase 45: Bubbles gateway dialogue text hook.

This is the first true data hook for the early Other World/Snakeway dialogue.
The main UTF-16 text bank is stored in a Webfoot container pointed to from
0x007B5B64. We decompress it, replace early King Yemma/Snakeway assistant text
with equal-length padded Bubbles Gateway text, append an uncompressed kind-0
container, and redirect the text-bank pointer.

No original text block is overwritten; the original compressed bank remains in
ROM as fallback.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase45_bubbles_dialogue_text_hook"
MANIFEST = ROOT / "additive_content" / "phase45_dialogue_text_hook" / "phase45_bubbles_dialogue_text_hook_manifest.json"
DOC = ROOT / "docs" / "PHASE45_BUBBLES_DIALOGUE_TEXT_HOOK.md"
DRAGONBYTEZ = ROOT / "tools" / "DragonByteZ" / "dragonbytez-cli"
TEXT_BANK_POINTER_OFFSET = 0x007B5B64
TEXT_BANK_ORIGINAL_VA = 0x0879BF2C
TEXT_BANK_ORIGINAL_OFFSET = 0x0079BF2C

REPLACEMENTS = [
    (
        "Welcome to King Yemma's Castle. You're going to want to talk to King Yemma.",
        "Bubbles guards the Rift Gate. Choose Super, GT, AF, LOG1 or LOG2.",
    ),
    (
        "Sir, you can't go this way!",
        "Bubbles opens Rift Gate!",
    ),
    (
        "Sir, you can't go this way! I'm afraid you're going to have to wait in line like...Wait a second!",
        "Bubbles: A rift is open. Super, GT, AF, LOG1 and LOG2 wait beyond Snake Way.",
    ),
    (
        "You still have your body!",
        "You can cross dimensions!",
    ),
    (
        "Please, go ahead!",
        "Choose a rift!",
    ),
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


def align(v: int, boundary: int) -> int:
    return (v + boundary - 1) & ~(boundary - 1)


def read_u32(data: bytes | bytearray, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def write_u32(data: bytearray, off: int, val: int) -> None:
    struct.pack_into("<I", data, off, val)


def decompress_text_bank() -> bytes:
    if not DRAGONBYTEZ.exists():
        raise SystemExit(f"Missing DragonByteZ CLI: {DRAGONBYTEZ}")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "text_bank.bin"
        subprocess.run([str(DRAGONBYTEZ), "decompress", str(BASE), hex(TEXT_BANK_ORIGINAL_OFFSET), "-o", str(out)], check=True, cwd=ROOT)
        return out.read_bytes()


def pad_text(new: str, old: str) -> str:
    if len(new) > len(old):
        raise ValueError(f"replacement too long: {new!r} > {old!r}")
    return new + (" " * (len(old) - len(new)))


def patch_text_bank(bank: bytes) -> tuple[bytes, list[dict]]:
    data = bytearray(bank)
    logs = []
    for old, new in REPLACEMENTS:
        old_raw = old.encode("utf-16le")
        idx = data.find(old_raw)
        if idx < 0:
            raise SystemExit(f"Could not find text in decompressed bank: {old!r}")
        new_raw = pad_text(new, old).encode("utf-16le")
        data[idx:idx + len(old_raw)] = new_raw
        logs.append({"offset_in_text_bank": f"0x{idx:04X}", "old": old, "new": new, "padded_chars": len(old) - len(new)})
    return bytes(data), logs


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base SHA-1 mismatch")
    if read_u32(base, TEXT_BANK_POINTER_OFFSET) != TEXT_BANK_ORIGINAL_VA:
        raise SystemExit("Text bank pointer precondition failed")
    bank = decompress_text_bank()
    patched_bank, replacements = patch_text_bank(bank)
    modified = bytearray(base)
    container_offset = align(len(modified), 4)
    modified.extend(b"\xFF" * (container_offset - len(modified)))
    container_va = 0x08000000 + container_offset
    modified.extend(struct.pack("<II", 0, len(patched_bank)))
    modified.extend(patched_bank)
    write_u32(modified, TEXT_BANK_POINTER_OFFSET, container_va)
    while len(modified) % 4:
        modified.append(0)
    final = bytes(modified)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    manifest = {
        "schema": "jurai.phase45.bubbles_dialogue_text_hook.v1",
        "policy": "append_uncompressed_text_bank_original_bank_preserved",
        "output_gba": gba.relative_to(ROOT).as_posix(),
        "output_ips": ips.relative_to(ROOT).as_posix(),
        "modified_sha1": hashlib.sha1(final).hexdigest(),
        "text_bank_pointer_offset": f"0x{TEXT_BANK_POINTER_OFFSET:06X}",
        "old_text_bank_va": f"0x{TEXT_BANK_ORIGINAL_VA:08X}",
        "new_text_bank_va": f"0x{container_va:08X}",
        "new_text_bank_container_offset": f"0x{container_offset:06X}",
        "decompressed_size": len(bank),
        "replacements": replacements,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Phase 45 — Bubbles dialogue text hook",
        "",
        "Decompressed the main text bank, replaced early King Yemma/Snakeway assistant dialogue with equal-length Bubbles Gateway text, appended it as an uncompressed Webfoot container, and redirected the text bank pointer.",
        "",
        f"Output ROM: `{gba.relative_to(ROOT)}`",
        f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`",
        f"New text bank VA: `0x{container_va:08X}`",
        f"Manifest: `{MANIFEST.relative_to(ROOT)}`",
        "",
        "## Replacements",
        "",
    ]
    for r in replacements:
        lines.append(f"- `{r['old']}` -> `{r['new']}` at {r['offset_in_text_bank']}")
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    txt.write_text(DOC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {gba}")


if __name__ == "__main__":
    main()
