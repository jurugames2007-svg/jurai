#!/usr/bin/env python3
"""Phase 31: real-gateway interaction contract payload."""
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
OUT_DIR = ROOT / "additive_content" / "phase31_gateway_interaction"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase31_gateway_interaction_payload"
DOC = ROOT / "docs" / "PHASE31_GATEWAY_INTERACTION_PAYLOAD.md"
MAGIC = b"LOG4GI31"
VERSION = 1
OPTIONS = ["SUPER_ROUTE", "GT_ROUTE", "AF_ROUTE", "LOG1_DIMENSION", "LOG2_DIMENSION"]


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
        raise SystemExit("Base SHA-1 mismatch")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    interaction = {
        "schema": "jurai.phase31.gateway_interaction.v1",
        "actor": "BUBBLES_GATE_GUIDE",
        "trigger_plan": "reuse confirmed early Other World/Snakeway dialogue interaction, then replace text branch with gateway options",
        "states": ["CLOSED", "OPENING_DIALOGUE", "OPTION_SELECT", "CONFIRM", "WARP_OR_ROUTE_SET", "RETURN"],
        "input": {"up_down": "move selection", "a": "confirm", "b": "cancel", "start": "debug unlock"},
        "options": [{"index": i, "target": opt, "sets_flag": f"ENTERED_{opt}"} for i, opt in enumerate(OPTIONS)],
        "native_work_remaining": ["identify text/script pointer for Bubbles dialogue", "implement cursor drawing or reuse native list menu", "bind option to map/route transition"],
    }
    path = OUT_DIR / "gateway_interaction_contract.json"
    path.write_text(json.dumps(interaction, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    text = "Bubbles: Choose a rift.\n-Super\n-GT\n-AF\n-LOG1 Dimension\n-LOG2 Dimension\n-End"
    bank = OUT_DIR / "gateway_interaction_text.utf16le.bin"
    bank.write_bytes(text.encode("utf-16le") + b"\x00\x00")
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(path, path.relative_to(ROOT).as_posix())
        zf.write(bank, bank.relative_to(ROOT).as_posix())
    payload = bio.getvalue()
    directory = json.dumps({"schema": "jurai.phase31.payload.v1", "files": [path.relative_to(ROOT).as_posix(), bank.relative_to(ROOT).as_posix()], "payload_sha1": hashlib.sha1(payload).hexdigest()}, separators=(",", ":")).encode("utf-8")
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
    manifest = {"schema": "jurai.phase31.gateway_interaction_build.v1", "output_gba": gba.relative_to(ROOT).as_posix(), "output_ips": ips.relative_to(ROOT).as_posix(), "modified_sha1": hashlib.sha1(final_b).hexdigest(), "contract": path.relative_to(ROOT).as_posix()}
    (OUT_DIR / "phase31_gateway_interaction_payload_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text(f"# Phase 31 — Gateway interaction payload\n\nOutput ROM: `{gba.relative_to(ROOT)}`\n\nModified SHA-1: `{hashlib.sha1(final_b).hexdigest()}`\n\nContract: `{path.relative_to(ROOT)}`\n", encoding="utf-8")
    txt.write_text(DOC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {gba}")


if __name__ == "__main__":
    main()
