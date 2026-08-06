#!/usr/bin/env python3
"""Phase 40: Gateway native hook blueprint and payload."""
from __future__ import annotations

import hashlib
import io
import json
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
OUT = ROOT / "additive_content" / "phase40_gateway_hook_blueprint"
DOC = ROOT / "docs" / "PHASE40_GATEWAY_HOOK_BLUEPRINT.md"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase40_gateway_hook_blueprint"
MAGIC = b"LOG4H40!"
VERSION = 1

BLUEPRINT = {
    "schema": "jurai.phase40.gateway_hook_blueprint.v1",
    "policy": "blueprint_payload_no_code_patch_yet",
    "hook_target": "early Other World/Bubbles dialogue decompression caller",
    "do_not_patch_globally": ["0x03000268 generic back-reference decompressor write", "0x03000060 generic literal writer"],
    "safe_strategy": [
        "Find compressed dialogue package pointer for early Bubbles/Other World text.",
        "Append replacement compressed or plain UTF-16 dialogue bank.",
        "Patch the caller's source pointer or data table, not the generic decompressor routine.",
        "Add a fallback flag: if LOG4 gateway flag unset, original pointer is used.",
    ],
    "gateway_text_lines": [
        "Bubbles: Choose a rift.",
        "-Super",
        "-GT",
        "-AF",
        "-LOG1 Dimension",
        "-LOG2 Dimension",
        "-End",
    ],
    "route_bindings": {
        "Super": "SUPER_ROUTE",
        "GT": "GT_ROUTE",
        "AF": "AF_ROUTE",
        "LOG1 Dimension": "LOG1_DIMENSION",
        "LOG2 Dimension": "LOG2_DIMENSION",
    },
}


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


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base ROM SHA-1 mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    blueprint_path = OUT / "gateway_hook_blueprint.json"
    blueprint_path.write_text(json.dumps(BLUEPRINT, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    bank_path = OUT / "gateway_menu_text.utf16le.bin"
    bank_path.write_bytes(("\n".join(BLUEPRINT["gateway_text_lines"])).encode("utf-16le") + b"\x00\x00")
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in [blueprint_path, bank_path]:
            zf.write(p, p.relative_to(ROOT).as_posix())
    payload = bio.getvalue()
    directory = json.dumps({"schema": "jurai.phase40.payload.v1", "files": [blueprint_path.relative_to(ROOT).as_posix(), bank_path.relative_to(ROOT).as_posix()], "payload_sha1": hashlib.sha1(payload).hexdigest()}, separators=(",", ":")).encode("utf-8")
    header = MAGIC + struct.pack("<III", VERSION, len(directory), len(payload))
    final = bytearray(base + header + directory + payload)
    while len(final) % 4:
        final.append(0)
    final_b = bytes(final)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final_b)
    ips.write_bytes(ips_patch(base, final_b))
    manifest = {"schema": "jurai.phase40.gateway_hook_blueprint_build.v1", "output_gba": gba.relative_to(ROOT).as_posix(), "output_ips": ips.relative_to(ROOT).as_posix(), "modified_sha1": hashlib.sha1(final_b).hexdigest(), "blueprint": blueprint_path.relative_to(ROOT).as_posix()}
    (OUT / "phase40_gateway_hook_blueprint_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Phase 40 — Gateway hook blueprint\n\n"
        "Prepared a concrete native-hook strategy: patch the dialogue source/caller, not the generic decompressor.\n\n"
        f"Output ROM: `{gba.relative_to(ROOT)}`\n\n"
        f"Modified SHA-1: `{hashlib.sha1(final_b).hexdigest()}`\n\n"
        f"Blueprint: `{blueprint_path.relative_to(ROOT)}`\n",
        encoding="utf-8",
    )
    txt.write_text(DOC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {gba}")


if __name__ == "__main__":
    main()
