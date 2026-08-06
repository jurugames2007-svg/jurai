#!/usr/bin/env python3
"""Phase 27: build a tester-facing release package.

The package gives the user a clear ROM to test plus the canonical/original-first
build and documentation. It does not build new gameplay; it prepares a reliable
handoff bundle.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "additive_content" / "release"
DOC = ROOT / "docs" / "PHASE27_TEST_RELEASE_PACKAGE.md"
OUT_ZIP = ROOT / "patch_output" / "LOG4_v0_1_bubbles_gateway_test_pack.zip"
MANIFEST = RELEASE_DIR / "v0_1_bubbles_gateway_manifest.json"

INCLUDE = [
    (ROOT / "patch_output" / "DBZ_LOG4_phase26_bubbles_start_gateway.gba", "roms/DBZ_LOG4_v0_1_DEBUG_BubblesGateway.gba"),
    (ROOT / "patch_output" / "DBZ_LOG4_phase26_bubbles_start_gateway.ips", "patches/DBZ_LOG4_v0_1_DEBUG_BubblesGateway.ips"),
    (ROOT / "patch_output" / "DBZ_LOG4_phase19_postgame_dimension_gateway.gba", "roms/DBZ_LOG4_v0_1_CANON_OriginalFirst.gba"),
    (ROOT / "patch_output" / "DBZ_LOG4_phase19_postgame_dimension_gateway.ips", "patches/DBZ_LOG4_v0_1_CANON_OriginalFirst.ips"),
    (ROOT / "patch_output" / "DBZ_LOG4_phase24_snakeway_multi_gatekeeper_probe.gba", "roms/experimental/DBZ_LOG4_phase24_multi_gatekeeper_probe.gba"),
    (ROOT / "docs" / "PHASE26_BUBBLES_START_GATEWAY.md", "docs/PHASE26_BUBBLES_START_GATEWAY.md"),
    (ROOT / "docs" / "PHASE25_LONG_RUNTIME_COMPARE.md", "docs/PHASE25_LONG_RUNTIME_COMPARE.md"),
    (ROOT / "docs" / "PHASE19_POSTGAME_DIMENSION_GATEWAY.md", "docs/PHASE19_POSTGAME_DIMENSION_GATEWAY.md"),
    (ROOT / "additive_content" / "gateway" / "bubbles_start_gateway_contract.json", "manifests/bubbles_start_gateway_contract.json"),
    (ROOT / "additive_content" / "gateway" / "postgame_dimension_gateway.json", "manifests/postgame_dimension_gateway.json"),
]

README = """# Dragon Ball: The Legacy of Goku 4 — v0.1 Bubbles Gateway Test Pack

## Recommended test ROM

Open this first in mGBA:

```text
roms/DBZ_LOG4_v0_1_DEBUG_BubblesGateway.gba
```

Expected visible debug text:

- `Bubbles!`
- `Bubbles Gateway`
- `Find Bubbles Gate`
- `Choose Bubbles Gate`

## Canon/original-first ROM

Use this to confirm the original early game remains intact:

```text
roms/DBZ_LOG4_v0_1_CANON_OriginalFirst.gba
```

## Experimental NPC probe

If you want to search Snakeway/Riftway for an injected NPC candidate:

```text
roms/experimental/DBZ_LOG4_phase24_multi_gatekeeper_probe.gba
```

This may not visibly show anything yet; it is an experimental native NPC-record probe.

## Current limitation

The Gateway is visible as text/debug data. A fully interactable Bubbles menu still requires decoding the native NPC/script trigger format.
"""


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def main() -> None:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for src, arc in INCLUDE:
        if src.exists():
            files.append({"source": src, "archive": arc, "sha1": sha1(src), "size": src.stat().st_size})
    readme_path = RELEASE_DIR / "v0_1_README.md"
    readme_path.write_text(README, encoding="utf-8")
    files.append({"source": readme_path, "archive": "README.md", "sha1": sha1(readme_path), "size": readme_path.stat().st_size})
    OUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for item in files:
            zf.write(item["source"], item["archive"])
    manifest = {
        "schema": "jurai.phase27.test_release.v1",
        "version": "v0.1-bubbles-gateway",
        "recommended_test_rom": "roms/DBZ_LOG4_v0_1_DEBUG_BubblesGateway.gba",
        "canonical_rom": "roms/DBZ_LOG4_v0_1_CANON_OriginalFirst.gba",
        "zip": OUT_ZIP.relative_to(ROOT).as_posix(),
        "zip_sha1": sha1(OUT_ZIP),
        "files": [{k: v for k, v in item.items() if k != "source"} for item in files],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Phase 27 — Test release package",
        "",
        "Built a tester-facing package for the current Bubbles Gateway milestone.",
        "",
        f"Package: `{OUT_ZIP.relative_to(ROOT)}`",
        f"SHA-1: `{sha1(OUT_ZIP)}`",
        "",
        "Recommended ROM inside package:",
        "",
        "```text",
        "roms/DBZ_LOG4_v0_1_DEBUG_BubblesGateway.gba",
        "```",
        "",
        f"Manifest: `{MANIFEST.relative_to(ROOT)}`",
    ]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_ZIP}")
    print(f"Wrote {MANIFEST}")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
