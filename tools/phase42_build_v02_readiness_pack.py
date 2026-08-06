#!/usr/bin/env python3
"""Phase 42: build v0.2 readiness package."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "patch_output" / "LOG4_v0_2_gateway_runtime_readiness_pack.zip"
DOC = ROOT / "docs" / "PHASE42_V02_READINESS_PACK.md"
MANIFEST = ROOT / "additive_content" / "phase42_readiness" / "v0_2_readiness_manifest.json"
FILES = [
    ROOT / "patch_output" / "DBZ_LOG4_phase26_bubbles_start_gateway.gba",
    ROOT / "patch_output" / "DBZ_LOG4_phase34_gateway_hook_research.gba",
    ROOT / "patch_output" / "DBZ_LOG4_phase31_gateway_interaction_payload.gba",
    ROOT / "patch_output" / "DBZ_LOG4_phase32_first_playable_route_package.gba",
    ROOT / "docs" / "PHASE39_DIALOGUE_TRACE_PACKAGE.md",
    ROOT / "docs" / "PHASE40_GATEWAY_HOOK_BLUEPRINT.md",
    ROOT / "docs" / "PHASE41_TRACE_VALIDATION_REPORT.md",
    ROOT / "docs" / "PROJECT_PHASES_REMAINING.md",
]

README = """# LOG4 v0.2 Gateway Runtime Readiness Pack

This package is for developers/testers preparing the next milestone: a real Bubbles Gateway menu.

Recommended user-facing ROM remains:

```text
DBZ_LOG4_phase26_bubbles_start_gateway.gba
```

Research ROM/payloads included:

- phase34 gateway hook research
- phase31 gateway interaction payload
- phase32 first route package

Next implementation target: patch the early dialogue source/caller so Bubbles opens the gateway menu.
"""


def sha1(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()


def main() -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    temp = MANIFEST.parent / "README_v0_2.md"
    temp.write_text(README, encoding="utf-8")
    entries = []
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(temp, "README.md")
        entries.append({"archive": "README.md", "sha1": sha1(temp), "size": temp.stat().st_size})
        for p in FILES:
            if p.exists():
                arc = p.relative_to(ROOT).as_posix()
                zf.write(p, arc)
                entries.append({"archive": arc, "sha1": sha1(p), "size": p.stat().st_size})
    manifest = {"schema": "jurai.phase42.v02_readiness_pack.v1", "zip": OUT.relative_to(ROOT).as_posix(), "zip_sha1": sha1(OUT), "files": entries}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Phase 42 — v0.2 readiness pack\n\n"
        f"Package: `{OUT.relative_to(ROOT)}`\n\n"
        f"SHA-1: `{sha1(OUT)}`\n\n"
        f"Manifest: `{MANIFEST.relative_to(ROOT)}`\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT} {sha1(OUT)}")


if __name__ == "__main__":
    main()
