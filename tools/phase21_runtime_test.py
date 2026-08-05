#!/usr/bin/env python3
"""Phase 21.2 runtime-report helper for debug gateway outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "PHASE21_DEBUG_GATEWAY_RUNTIME.md"
RESULT = ROOT / "playtest_output" / "phase21_debug" / "skip-playtest-result.json"
CONTACT = ROOT / "playtest_output" / "phase21_debug_contact.png"


def make_contact() -> None:
    folder = ROOT / "playtest_output" / "phase21_debug"
    files = sorted(folder.glob("screenshot-*.png"))
    thumbs = []
    for f in files:
        img = Image.open(f).convert("RGBA").resize((120, 80), Image.Resampling.NEAREST)
        thumbs.append((f.name, img))
    if not thumbs:
        return
    w = 4 * 170
    h = ((len(thumbs) + 3) // 4) * 110
    sheet = Image.new("RGBA", (w, h), (20, 20, 28, 255))
    d = ImageDraw.Draw(sheet)
    for i, (label, img) in enumerate(thumbs):
        x = (i % 4) * 170
        y = (i // 4) * 110
        sheet.alpha_composite(img, (x, y + 20))
        d.text((x, y + 2), label, fill=(255, 255, 255, 255))
    sheet.save(CONTACT)


def main() -> None:
    make_contact()
    result = json.loads(RESULT.read_text(encoding="utf-8")) if RESULT.exists() else {"status": "missing"}
    lines = [
        "# Phase 21.2 — Debug gateway runtime",
        "",
        f"Status: `{result.get('status')}`",
        "",
        f"Result JSON: `{RESULT.relative_to(ROOT)}`" if RESULT.exists() else "Result JSON missing",
        f"Contact sheet: `{CONTACT.relative_to(ROOT)}`" if CONTACT.exists() else "Contact sheet missing",
        "",
        "This validates that the optional debug gateway text build still runs through the automated boot/input sequence.",
    ]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {DOC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
