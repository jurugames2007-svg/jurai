#!/usr/bin/env python3
"""Phase 52: package the v0.3 playable warp-room release."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE51_SCRIPT = ROOT / "tools" / "phase51_boot_gateway_warp_rooms.py"
GBA = ROOT / "patch_output" / "DBZ_LOG4_phase51_boot_gateway_warp_rooms.gba"
IPS = ROOT / "patch_output" / "DBZ_LOG4_phase51_boot_gateway_warp_rooms.ips"
PHASE51_DOC = ROOT / "docs" / "PHASE51_BOOT_GATEWAY_WARP_ROOMS.md"
PHASE51_MANIFEST = ROOT / "additive_content" / "gateway_warp_rooms" / "phase51_boot_gateway_warp_rooms_manifest.json"
DOC = ROOT / "docs" / "PHASE52_V03_PLAYABLE_WARP_ROOMS_RELEASE.md"
MANIFEST = ROOT / "additive_content" / "release" / "v0_3_playable_warp_rooms_manifest.json"
ZIP = ROOT / "patch_output" / "LOG4_v0_3_playable_warp_rooms_pack.zip"
README = ROOT / "patch_output" / "LOG4_v0_3_PLAYABLE_WARP_ROOMS_README.txt"

RUNTIME_EVIDENCE = [
    ROOT / "playtest_output" / "phase51_warp_rooms" / "phase51-warp-rooms-result.json",
    ROOT / "playtest_output" / "phase51_warp_rooms" / "screenshot-00_gateway_original.png",
    ROOT / "playtest_output" / "phase51_warp_rooms" / "screenshot-02_super_room_spawn.png",
    ROOT / "playtest_output" / "phase51_warp_rooms" / "screenshot-05_log1_room_after_r_cycle.png",
    ROOT / "playtest_output" / "phase51_warp_rooms" / "screenshot-08_log2_on_home_pad.png",
    ROOT / "playtest_output" / "phase51_warp_rooms" / "screenshot-11_original_boot_after_start.png",
]


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def run_phase51() -> None:
    subprocess.run([sys.executable, str(PHASE51_SCRIPT)], cwd=ROOT, check=True)


def main() -> int:
    run_phase51()
    required = [GBA, IPS, PHASE51_DOC, PHASE51_MANIFEST]
    missing = [p for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing phase 51 artifacts: " + ", ".join(str(p) for p in missing))

    gba_sha1 = sha1(GBA)
    ips_sha1 = sha1(IPS)

    README.write_text(
        "Dragon Ball: The Legacy of Goku 4 — v0.3 Playable Warp Rooms\n"
        "==============================================================\n\n"
        "Recommended test ROM:\n"
        "  roms/DBZ_LOG4_v0_3_PlayableWarpRooms.gba\n\n"
        f"ROM SHA-1: {gba_sha1}\n"
        f"IPS SHA-1: {ips_sha1}\n\n"
        "What works in this debug build:\n"
        "- Boot-time Gateway selector appears immediately.\n"
        "- ORIGINAL boots the untouched Buu's Fury entry point.\n"
        "- SUPER / GT / AF / LOG1 DIM / LOG2 DIM open playable route rooms.\n"
        "- D-pad moves a tester marker inside each room.\n"
        "- A on HOME returns to Gateway.\n"
        "- A on NEXT warps to the next dimension room.\n"
        "- L/R cycles route rooms.\n"
        "- A on ORIG, or Start in any room, boots original Buu's Fury.\n\n"
        "Honest limitation:\n"
        "This is a real runtime/playable appended hook, but route rooms are still a safe debug layer.\n"
        "They do not yet call Buu's Fury native map transition code. Native map warps are the next target.\n",
        encoding="utf-8",
    )

    DOC.write_text(
        "# Phase 52 — v0.3 Playable Warp Rooms Release\n\n"
        "Packaged Phase 51 as the v0.3 debug release for tester handoff.\n\n"
        "## Recommended file to test\n\n"
        "`patch_output/LOG4_v0_3_playable_warp_rooms_pack.zip` → `roms/DBZ_LOG4_v0_3_PlayableWarpRooms.gba`\n\n"
        "## Checksums\n\n"
        f"- ROM SHA-1: `{gba_sha1}`\n"
        f"- IPS SHA-1: `{ips_sha1}`\n"
        "- ZIP SHA-1: see `additive_content/release/v0_3_playable_warp_rooms_manifest.json` after package build.\n\n"
        "## Runtime coverage\n\n"
        "The package includes the Phase 51 runtime evidence when present. The headless test covers: Gateway boot, entering a room, moving the marker, L/R room cycling, pad warp, HOME return, and Start fallback into original Buu's Fury.\n\n"
        "## Status\n\n"
        "Playable debug warp layer: **yes**. Native Buu's Fury map loader warp: **not yet**. Base/original fallback: **yes**.\n",
        encoding="utf-8",
    )

    files: list[tuple[Path, str]] = [
        (GBA, "roms/DBZ_LOG4_v0_3_PlayableWarpRooms.gba"),
        (IPS, "patches/DBZ_LOG4_v0_3_PlayableWarpRooms.ips"),
        (README, "README.txt"),
        (PHASE51_DOC, "docs/PHASE51_BOOT_GATEWAY_WARP_ROOMS.md"),
        (DOC, "docs/PHASE52_V03_PLAYABLE_WARP_ROOMS_RELEASE.md"),
        (PHASE51_MANIFEST, "manifests/phase51_boot_gateway_warp_rooms_manifest.json"),
    ]
    for ev in RUNTIME_EVIDENCE:
        if ev.exists():
            files.append((ev, "runtime_evidence/" + ev.name))

    ZIP.parent.mkdir(parents=True, exist_ok=True)
    tmp = ZIP.with_suffix(".zip.tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in files:
            zf.write(src, arc)
    if ZIP.exists():
        ZIP.unlink()
    tmp.rename(ZIP)
    zip_sha1 = sha1(ZIP)

    manifest = {
        "schema": "jurai.release.v0_3_playable_warp_rooms.v1",
        "package": ZIP.relative_to(ROOT).as_posix(),
        "package_sha1": zip_sha1,
        "recommended_rom_in_zip": "roms/DBZ_LOG4_v0_3_PlayableWarpRooms.gba",
        "rom_sha1": gba_sha1,
        "ips_sha1": ips_sha1,
        "source_phase": 51,
        "release_phase": 52,
        "playable": True,
        "native_map_warp": False,
        "original_fallback": True,
        "included_files": [arc for _, arc in files],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {ZIP.relative_to(ROOT)}")
    print(f"ROM SHA-1 {gba_sha1}")
    print(f"ZIP SHA-1 {zip_sha1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
