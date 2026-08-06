#!/usr/bin/env python3
"""Phase 21.0: route start profiles.

Defines how the player should be able to start from the original line, post-Kid
Buu routes, and LOG1/LOG2 dimensions. This is data-only and will be consumed by
future gateway/debug-start hooks.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "additive_content" / "gateway" / "route_start_profiles.json"
DOC = ROOT / "docs" / "PHASE21_ROUTE_START_PROFILES.md"

PROFILES = [
    {
        "id": "START_ORIGINAL_BUUS_FURY",
        "label": "Buu's Fury Original",
        "line_position": "mainline",
        "intended_access": "default new game / continue",
        "sets_flags": [],
        "target": {"type": "native_original_flow", "description": "Do not alter early game."},
    },
    {
        "id": "START_GATEWAY_DEBUG",
        "label": "Rift Gateway Debug",
        "line_position": "debug",
        "intended_access": "debug build only until post-Kid-Buu unlock is hooked",
        "sets_flags": ["LOG4_DEBUG_GATEWAY_UNLOCKED", "LOG4_POSTGAME_GATEWAY_UNLOCKED"],
        "target": {"type": "gateway_menu", "id": "CAPSULE_CORP_RIFT_GATEWAY"},
    },
    {
        "id": "START_SUPER_POST_BUU",
        "label": "Super Route",
        "line_position": "post_kid_buu",
        "sets_flags": ["STORY_KID_BUU_DEFEATED", "STORY_SUPER_START", "LOG4_ROUTE_SUPER_UNLOCKED"],
        "target": {"type": "route", "id": "SUPER_ROUTE"},
    },
    {
        "id": "START_GT_POST_BUU",
        "label": "GT Route",
        "line_position": "post_kid_buu",
        "sets_flags": ["STORY_KID_BUU_DEFEATED", "STORY_GT_START", "LOG4_ROUTE_GT_UNLOCKED", "LOG4_BLACK_STAR_RADAR"],
        "target": {"type": "route", "id": "GT_ROUTE"},
    },
    {
        "id": "START_AF_POST_BUU",
        "label": "AF Route",
        "line_position": "post_kid_buu",
        "sets_flags": ["STORY_KID_BUU_DEFEATED", "STORY_AF_START", "LOG4_ROUTE_AF_UNLOCKED"],
        "target": {"type": "route", "id": "AF_ROUTE"},
    },
    {
        "id": "START_LOG1_DIMENSION",
        "label": "LOG1 Dimension",
        "line_position": "pre_kid_buu_dimension",
        "sets_flags": ["DIMENSION_GATEWAY_UNLOCKED", "DIM_LOG1_UNLOCKED", "DIM_LOG1_ENTERED"],
        "target": {"type": "dimension", "id": "LOG1_DIMENSION"},
    },
    {
        "id": "START_LOG2_DIMENSION",
        "label": "LOG2 Dimension",
        "line_position": "pre_kid_buu_dimension",
        "sets_flags": ["DIMENSION_GATEWAY_UNLOCKED", "DIM_LOG2_UNLOCKED", "DIM_LOG2_ENTERED"],
        "target": {"type": "dimension", "id": "LOG2_DIMENSION"},
    },
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": "jurai.phase21.route_start_profiles.v1",
        "policy": "original_first_with_debug_start_profiles",
        "canonical_order": ["START_ORIGINAL_BUUS_FURY", "START_SUPER_POST_BUU", "START_GT_POST_BUU", "START_AF_POST_BUU", "START_LOG1_DIMENSION", "START_LOG2_DIMENSION"],
        "profiles": PROFILES,
        "notes": [
            "Story mode should always start with original Buu's Fury.",
            "Debug gateway can start anywhere during development.",
            "LOG1/LOG2 are dimensions, not replacements for the mainline.",
        ],
    }
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Phase 21.0 — Route start profiles",
        "",
        "Defines start profiles for original line, post-Kid-Buu routes and LOG1/LOG2 dimensions.",
        "",
        f"Output: `{OUT.relative_to(ROOT)}`",
        "",
        "## Profiles",
        "",
    ]
    for profile in PROFILES:
        lines.append(f"- `{profile['id']}` — {profile['label']} -> {profile['target']}")
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {DOC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
