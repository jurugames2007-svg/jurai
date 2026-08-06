#!/usr/bin/env python3
"""Phase 29: seed manual asset review with a safe first approval pass.

This does not claim final pixel-perfect approval. It separates Phase 28 assets
into:
- READY_FOR_ROM_TEST_DRAFT: icons, portraits and map previews that are native-sized
  and safe for data-bank experiments.
- NEEDS_PIXEL_CLEANUP: full character/enemy sprite sheets that still require
  manual pixel-by-pixel review before final insertion.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "additive_content" / "final_asset_kit"
QUEUE = KIT / "review" / "phase28_asset_review_queue.csv"
OUT_DIR = ROOT / "additive_content" / "phase29_review"
DOC = ROOT / "docs" / "PHASE29_ASSET_REVIEW_SEED.md"
READY_CATEGORIES = {"portrait", "item_icon", "technique_icon", "map_preview"}
BLOCKED_CATEGORIES = {"playable_sheet", "enemy_sheet"}


def image_info(rel: str) -> dict:
    p = ROOT / rel
    if not p.exists():
        return {"exists": False}
    with Image.open(p) as im:
        return {"exists": True, "width": im.width, "height": im.height, "mode": im.mode, "sha1_source": rel}


def make_contact(rows: list[dict], path: Path) -> None:
    thumbs = []
    for row in rows[:80]:
        p = ROOT / row["file"]
        if not p.exists() or p.suffix.lower() != ".png":
            continue
        im = Image.open(p).convert("RGBA")
        im.thumbnail((56, 56), Image.Resampling.NEAREST)
        thumbs.append((row["asset_id"], row["category"], im))
    if not thumbs:
        return
    cols = 5
    w = cols * 150
    h = ((len(thumbs) + cols - 1) // cols) * 84 + 24
    sheet = Image.new("RGBA", (w, h), (18, 20, 30, 255))
    d = ImageDraw.Draw(sheet)
    d.text((5, 5), "Phase 29 READY_FOR_ROM_TEST_DRAFT sample", fill=(255, 235, 140, 255))
    for i, (asset_id, category, im) in enumerate(thumbs):
        x = (i % cols) * 150
        y = 24 + (i // cols) * 84
        sheet.alpha_composite(im, (x + 4, y + 18))
        d.text((x + 4, y), asset_id[:18], fill=(230, 238, 255, 255))
        d.text((x + 4, y + 64), category[:18], fill=(128, 220, 255, 255))
    sheet.save(path, optimize=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with QUEUE.open(newline="", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    ready = []
    blocked = []
    updated_rows = []
    for row in rows:
        info = image_info(row["file"])
        new = dict(row)
        new.update(info)
        if row["category"] in READY_CATEGORIES and info.get("exists"):
            new["status"] = "READY_FOR_ROM_TEST_DRAFT"
            ready.append(new)
        elif row["category"] in BLOCKED_CATEGORIES:
            new["status"] = "NEEDS_PIXEL_CLEANUP"
            blocked.append(new)
        else:
            new["status"] = "TODO_REVIEW"
        updated_rows.append(new)
    updated_csv = OUT_DIR / "phase29_review_queue_seeded.csv"
    fields = list(updated_rows[0].keys())
    with updated_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(updated_rows)
    contact = OUT_DIR / "phase29_ready_draft_contact.png"
    make_contact(ready, contact)
    manifest = {
        "schema": "jurai.phase29.asset_review_seed.v1",
        "policy": "draft_ready_assets_only_final_sprites_require_manual_cleanup",
        "source_queue": QUEUE.relative_to(ROOT).as_posix(),
        "updated_queue": updated_csv.relative_to(ROOT).as_posix(),
        "ready_for_rom_test_draft_count": len(ready),
        "needs_pixel_cleanup_count": len(blocked),
        "ready_assets": ready,
        "blocked_sprite_sheets": blocked,
        "contact_sheet": contact.relative_to(ROOT).as_posix() if contact.exists() else "",
    }
    manifest_path = OUT_DIR / "phase29_asset_review_seed_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Phase 29 — Asset review seed\n\n"
        f"Ready draft assets: {len(ready)}\n\n"
        f"Sprite sheets needing cleanup: {len(blocked)}\n\n"
        "Icons, portraits and map previews are marked `READY_FOR_ROM_TEST_DRAFT` for native bank experiments. "
        "Full character/enemy sheets remain `NEEDS_PIXEL_CLEANUP` until manual pixel review.\n\n"
        f"Manifest: `{manifest_path.relative_to(ROOT)}`\n\n"
        f"Queue: `{updated_csv.relative_to(ROOT)}`\n\n"
        f"Contact: `{contact.relative_to(ROOT) if contact.exists() else ''}`\n",
        encoding="utf-8",
    )
    print(f"Wrote {manifest_path.relative_to(ROOT)}")
    print(f"Ready draft assets: {len(ready)}; blocked sprite sheets: {len(blocked)}")


if __name__ == "__main__":
    main()
