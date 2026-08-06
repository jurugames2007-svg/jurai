#!/usr/bin/env python3
"""Phase 55: package the v0.3.1 native-registry debug release."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE54_SCRIPT = ROOT / "tools" / "phase54_register_native_map_stubs.py"
GBA = ROOT / "patch_output" / "DBZ_LOG4_phase54_gateway_native_map_registry.gba"
IPS = ROOT / "patch_output" / "DBZ_LOG4_phase54_gateway_native_map_registry.ips"
PHASE51_GBA = ROOT / "patch_output" / "DBZ_LOG4_phase51_boot_gateway_warp_rooms.gba"
PHASE54_DOC = ROOT / "docs" / "PHASE54_GATEWAY_NATIVE_MAP_REGISTRY.md"
PHASE53_RUNTIME_DOC = ROOT / "docs" / "PHASE53_RUNTIME_NATIVE_MAP_TRACE.md"
PHASE54_MANIFEST = ROOT / "additive_content" / "phase54_native_map_registry" / "phase54_gateway_native_map_registry_manifest.json"
PHASE53_RUNTIME = ROOT / "additive_content" / "phase53_native_map_trace" / "phase53_runtime_trace_report.json"
DOC = ROOT / "docs" / "PHASE55_V031_NATIVE_REGISTRY_RELEASE.md"
MANIFEST = ROOT / "additive_content" / "release" / "v0_3_1_native_registry_manifest.json"
ZIP = ROOT / "patch_output" / "LOG4_v0_3_1_native_registry_pack.zip"
README = ROOT / "patch_output" / "LOG4_v0_3_1_NATIVE_REGISTRY_README.txt"

RUNTIME_EVIDENCE = [
    ROOT / "playtest_output" / "phase54_warp_rooms" / "phase51-warp-rooms-result.json",
    ROOT / "playtest_output" / "phase54_warp_rooms" / "screenshot-02_super_room_spawn.png",
    ROOT / "playtest_output" / "phase54_warp_rooms" / "screenshot-05_log1_room_after_r_cycle.png",
    ROOT / "playtest_output" / "phase54_warp_rooms" / "screenshot-09_gateway_returned_from_home.png",
    ROOT / "playtest_output" / "phase54_original_fallback_skip" / "skip-playtest-result.json",
    ROOT / "playtest_output" / "phase54_original_fallback_skip" / "screenshot-final.png",
]
FIXED_ZIP_TIME = (2026, 8, 5, 12, 0, 0)


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def run_phase54() -> None:
    subprocess.run([sys.executable, str(PHASE54_SCRIPT)], cwd=ROOT, check=True)


def write_deterministic_zip(entries: list[tuple[Path, str]]) -> None:
    tmp = ZIP.with_suffix(".zip.tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in sorted(entries, key=lambda item: item[1]):
            info = zipfile.ZipInfo(arc, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, src.read_bytes())
    if ZIP.exists():
        ZIP.unlink()
    tmp.rename(ZIP)


def main() -> int:
    run_phase54()
    for p in [GBA, IPS, PHASE51_GBA, PHASE54_DOC, PHASE54_MANIFEST, PHASE53_RUNTIME_DOC, PHASE53_RUNTIME]:
        if not p.exists():
            raise SystemExit(f"Missing artifact: {p}")

    gba_sha1 = sha1(GBA)
    ips_sha1 = sha1(IPS)
    phase51_sha1 = sha1(PHASE51_GBA)

    README.write_text(
        "Dragon Ball: The Legacy of Goku 4 — v0.3.1 Native Registry Debug Pack\n"
        "=====================================================================\n\n"
        "Recommended advanced test ROM:\n"
        "  roms/DBZ_LOG4_v0_3_1_NativeRegistry.gba\n\n"
        f"ROM SHA-1: {gba_sha1}\n"
        f"IPS SHA-1: {ips_sha1}\n\n"
        "What works:\n"
        "- Same playable boot Gateway warp-room layer as v0.3.\n"
        "- ORIGINAL/Start fallback still boots the untouched Buu's Fury flow.\n"
        "- Native AreaEntry table is extended additively from 452 to 457 entries.\n"
        "- Route IDs F0:01..F0:05 are registered for SUPER/GT/AF/LOG1/LOG2.\n\n"
        "Honest limitation:\n"
        "- Gateway selections still enter debug rooms. They do not yet call the native map constructor.\n"
        "- This pack is the bridge toward true native map warps, not the final native warp implementation.\n",
        encoding="utf-8",
    )

    DOC.write_text(
        "# Phase 55 — v0.3.1 Native Registry Release\n\n"
        "Phase 55 packages the Phase 54 advanced debug build. It keeps the playable v0.3 boot warp rooms and adds the first additive native map registry for route IDs.\n\n"
        "## Recommended advanced ROM\n\n"
        "`patch_output/LOG4_v0_3_1_native_registry_pack.zip` → `roms/DBZ_LOG4_v0_3_1_NativeRegistry.gba`\n\n"
        "## Checksums\n\n"
        f"- ROM SHA-1: `{gba_sha1}`\n"
        f"- IPS SHA-1: `{ips_sha1}`\n"
        f"- Base playable v0.3/Phase51 SHA-1: `{phase51_sha1}`\n\n"
        "## Status\n\n"
        "- Playable Gateway rooms: **yes**.\n"
        "- Original game fallback: **yes**.\n"
        "- Native map IDs registered additively: **yes**.\n"
        "- Gateway-to-native-map warp: **not yet**.\n\n"
        "## Why this matters\n\n"
        "Phase 53 proved the native AreaEntry lookup path. Phase 54 registers route-specific native IDs (`F0:01` through `F0:05`) without replacing original entries. The next step is to steer the constructor around `0x08009030` from the Gateway into one of these IDs or a known safe original map pair.\n",
        encoding="utf-8",
    )

    entries: list[tuple[Path, str]] = [
        (GBA, "roms/DBZ_LOG4_v0_3_1_NativeRegistry.gba"),
        (IPS, "patches/DBZ_LOG4_v0_3_1_NativeRegistry.ips"),
        (README, "README.txt"),
        (DOC, "docs/PHASE55_V031_NATIVE_REGISTRY_RELEASE.md"),
        (PHASE54_DOC, "docs/PHASE54_GATEWAY_NATIVE_MAP_REGISTRY.md"),
        (PHASE53_RUNTIME_DOC, "docs/PHASE53_RUNTIME_NATIVE_MAP_TRACE.md"),
        (PHASE54_MANIFEST, "manifests/phase54_gateway_native_map_registry_manifest.json"),
        (PHASE53_RUNTIME, "manifests/phase53_runtime_trace_report.json"),
    ]
    for ev in RUNTIME_EVIDENCE:
        if ev.exists():
            entries.append((ev, "runtime_evidence/" + ev.parent.name + "_" + ev.name))

    write_deterministic_zip(entries)
    zip_sha1 = sha1(ZIP)

    manifest = {
        "schema": "jurai.release.v0_3_1_native_registry.v1",
        "package": ZIP.relative_to(ROOT).as_posix(),
        "package_sha1": zip_sha1,
        "recommended_rom_in_zip": "roms/DBZ_LOG4_v0_3_1_NativeRegistry.gba",
        "rom_sha1": gba_sha1,
        "ips_sha1": ips_sha1,
        "source_phase": 54,
        "release_phase": 55,
        "playable_gateway_rooms": True,
        "native_map_registry": True,
        "native_map_warp": False,
        "original_fallback": True,
        "included_files": [arc for _, arc in sorted(entries, key=lambda item: item[1])],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {ZIP.relative_to(ROOT)}")
    print(f"ROM SHA-1 {gba_sha1}")
    print(f"ZIP SHA-1 {zip_sha1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
