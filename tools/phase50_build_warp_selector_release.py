#!/usr/bin/env python3
"""Phase 50: package the working boot-time warp selector.

The actual runtime hook was implemented in Phase 49. This phase packages that
hook as the v0.2 Warp Selector build for testers and records the remaining
native-map-warp requirement.
"""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROM=ROOT/'patch_output/DBZ_LOG4_phase49_boot_gateway_menu.gba'
IPS=ROOT/'patch_output/DBZ_LOG4_phase49_boot_gateway_menu.ips'
OUT=ROOT/'patch_output/LOG4_v0_2_boot_warp_selector_pack.zip'
MAN=ROOT/'additive_content/release/v0_2_boot_warp_selector_manifest.json'
DOC=ROOT/'docs/PHASE50_BOOT_WARP_SELECTOR_RELEASE.md'
README='''# LOG4 v0.2 Boot Warp Selector\n\nRecommended ROM:\n\n```text\nroms/DBZ_LOG4_v0_2_BootWarpSelector.gba\n```\n\nControls:\n\n- Up/Down: select warp point.\n- A/Start on Original: boot Buu's Fury.\n- A/Start on Super/GT/AF/LOG1/LOG2: open that route/dimension debug screen.\n- B: return to menu.\n- Start on route screen: boot Buu's Fury.\n\nCurrent limitation: route/dimension options are debug screens. Native map transitions are the next hook.\n'''
def sha1(p): return hashlib.sha1(p.read_bytes()).hexdigest()
def main():
 if not ROM.exists(): raise SystemExit('Missing phase49 ROM. Run phase49 first.')
 MAN.parent.mkdir(parents=True,exist_ok=True)
 readme=MAN.parent/'v0_2_boot_warp_selector_README.md'; readme.write_text(README,encoding='utf-8')
 with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.write(ROM,'roms/DBZ_LOG4_v0_2_BootWarpSelector.gba')
  if IPS.exists(): z.write(IPS,'patches/DBZ_LOG4_v0_2_BootWarpSelector.ips')
  z.write(readme,'README.md')
  for doc in ['docs/PHASE49_BOOT_GATEWAY_MENU.md','docs/PHASE49_RUNTIME_REPORT.md']:
   p=ROOT/doc
   if p.exists(): z.write(p,doc)
 manifest={'schema':'jurai.phase50.boot_warp_selector_release.v1','zip':OUT.relative_to(ROOT).as_posix(),'zip_sha1':sha1(OUT),'rom':ROM.relative_to(ROOT).as_posix(),'rom_sha1':sha1(ROM),'status':'working_boot_selector_debug_route_screens'}
 MAN.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 DOC.write_text(f"# Phase 50 — Boot Warp Selector Release\n\nPackaged the working Phase 49 boot-time selector as v0.2.\n\nPackage: `{OUT.relative_to(ROOT)}`\n\nSHA-1: `{sha1(OUT)}`\n\nROM: `{ROM.relative_to(ROOT)}`\n\nROM SHA-1: `{sha1(ROM)}`\n\nNext: native map transitions for each warp point.\n",encoding='utf-8')
 print(f'Wrote {OUT} {sha1(OUT)}')
if __name__=='__main__': main()
