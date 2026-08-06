#!/usr/bin/env python3
"""Phase 35: runtime route test plan.

Creates a test matrix for the first LOG2 route and gateway interaction so manual
and automated QA can run the same route checks.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "additive_content" / "phase35_runtime_tests"
DOC = ROOT / "docs" / "PHASE35_RUNTIME_ROUTE_TEST_PLAN.md"

TESTS = [
    {"id": "BOOT_ORIGINAL", "rom": "patch_output/DBZ_LOG4_phase26_bubbles_start_gateway.gba", "goal": "Boot to Bubbles Gateway debug title", "expected": ["Bubbles!", "Bubbles Gateway"]},
    {"id": "GATEWAY_TEXT", "rom": "patch_output/DBZ_LOG4_phase26_bubbles_start_gateway.gba", "goal": "Verify objective text", "expected": ["Find Bubbles Gate", "Choose Bubbles Gate"]},
    {"id": "LOG2_ROUTE_DATA", "rom": "patch_output/DBZ_LOG4_phase32_first_playable_route_package.gba", "goal": "Verify LOG2 route payload exists", "expected": ["LOG2_DIMENSION_CELL_GAMES_MEMORY_MINI_ROUTE"]},
    {"id": "ASSET_BANK", "rom": "patch_output/DBZ_LOG4_phase30_reviewed_asset_bank.gba", "goal": "Verify 108 ready draft assets packed", "expected": ["phase30 asset bank manifest record_count >= 108"]},
    {"id": "FULL_MATRIX", "rom": "patch_output/DBZ_LOG4_phase33_full_route_expansion_matrix.gba", "goal": "Verify all five routes are represented", "expected": ["SUPER_ROUTE", "GT_ROUTE", "AF_ROUTE", "LOG1_DIMENSION", "LOG2_DIMENSION"]},
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = {"schema": "jurai.phase35.runtime_route_test_plan.v1", "tests": TESTS, "status": "plan_ready_runtime_hooks_pending"}
    path = OUT_DIR / "runtime_route_test_plan.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text("# Phase 35 — Runtime route test plan\n\n" +
                   "Created a shared runtime test matrix for Bubbles Gateway, LOG2 first route, asset bank and full route matrix.\n\n" +
                   f"Plan: `{path.relative_to(ROOT)}`\n", encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
