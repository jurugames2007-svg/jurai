#!/usr/bin/env python3
"""Phase 30: build a native-oriented asset bank from Phase 29 reviewed drafts."""
from __future__ import annotations

import csv
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rom_base" / "DBZ_Buus_Fury_USA.gba"
BASE_SHA1 = "f1c4b07554d2a3b1ad2f325307051e775ce68087"
QUEUE = ROOT / "additive_content" / "phase29_review" / "phase29_review_queue_seeded.csv"
OUT_PREFIX = ROOT / "patch_output" / "DBZ_LOG4_phase30_reviewed_asset_bank"
OUT_DIR = ROOT / "additive_content" / "phase30_native_bank"
DOC = ROOT / "docs" / "PHASE30_REVIEWED_ASSET_BANK.md"
MAGIC = b"LOG4AB30"
VERSION = 1


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


def to_tile_order(indices: bytes, w: int, h: int) -> bytes:
    raw = bytearray()
    for ty in range(0, h, 8):
        for tx in range(0, w, 8):
            for y in range(8):
                start = (ty + y) * w + tx
                raw.extend(indices[start:start + 8])
    return bytes(raw)


def encode_png(path: Path) -> tuple[bytes, bytes, int, int]:
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    if w % 8 or h % 8:
        raise ValueError(f"Not tile aligned: {path} {im.size}")
    pal_img = im.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
    palette = bytes(pal_img.getpalette()[:256 * 3])
    indices = bytes(pal_img.getdata())
    return to_tile_order(indices, w, h), palette, w, h


def main() -> None:
    base = BASE.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        raise SystemExit("Base SHA-1 mismatch")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with QUEUE.open(newline="", encoding="utf-8") as fp:
        rows = [r for r in csv.DictReader(fp) if r["status"] == "READY_FOR_ROM_TEST_DRAFT"]
    payload = bytearray()
    records = []
    for row in rows:
        p = ROOT / row["file"]
        if not p.exists() or p.suffix.lower() != ".png":
            continue
        try:
            data, palette, w, h = encode_png(p)
        except Exception as exc:
            records.append({"asset_id": row["asset_id"], "category": row["category"], "source": row["file"], "status": "skipped", "reason": str(exc)})
            continue
        while len(payload) % 4:
            payload.append(0)
        data_off = len(payload)
        payload.extend(data)
        while len(payload) % 4:
            payload.append(0)
        pal_off = len(payload)
        payload.extend(palette)
        records.append({
            "asset_id": row["asset_id"],
            "category": row["category"],
            "source": row["file"],
            "status": "encoded",
            "format": "8bpp_tile_order_adaptive_palette",
            "width": w,
            "height": h,
            "data_offset": data_off,
            "data_size": len(data),
            "palette_offset": pal_off,
            "palette_size": len(palette),
            "sha1": hashlib.sha1(data).hexdigest(),
        })
    directory = {"schema": "jurai.phase30.reviewed_asset_bank.v1", "record_count": len(records), "records": records}
    directory_blob = json.dumps(directory, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    header = MAGIC + struct.pack("<III", VERSION, len(directory_blob), len(payload))
    modified = bytearray(base + header + directory_blob + bytes(payload))
    while len(modified) % 4:
        modified.append(0)
    final = bytes(modified)
    gba = OUT_PREFIX.with_suffix(".gba")
    ips = OUT_PREFIX.with_suffix(".ips")
    txt = OUT_PREFIX.with_suffix(".txt")
    gba.write_bytes(final)
    ips.write_bytes(ips_patch(base, final))
    manifest = {**directory, "output_gba": gba.relative_to(ROOT).as_posix(), "output_ips": ips.relative_to(ROOT).as_posix(), "modified_sha1": hashlib.sha1(final).hexdigest(), "payload_size": len(payload), "directory_size": len(directory_blob)}
    manifest_path = OUT_DIR / "phase30_reviewed_asset_bank_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    encoded = sum(1 for r in records if r.get("status") == "encoded")
    DOC.write_text(
        "# Phase 30 — Reviewed draft asset bank\n\n"
        f"Encoded records: {encoded}\n\n"
        f"Output ROM: `{gba.relative_to(ROOT)}`\n\n"
        f"Modified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n\n"
        f"Manifest: `{manifest_path.relative_to(ROOT)}`\n",
        encoding="utf-8",
    )
    txt.write_text(DOC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {gba}")
    print(f"Encoded records: {encoded}")


if __name__ == "__main__":
    main()
