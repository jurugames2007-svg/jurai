#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'rom_base/DBZ_Buus_Fury_USA.gba'
BASE_SHA1='f1c4b07554d2a3b1ad2f325307051e775ce68087'
REPORT=ROOT/'docs/PROJECT_DOCTOR_REPORT.md'
ROMS=[
 ('phase19_gateway',ROOT/'patch_output/DBZ_LOG4_phase19_postgame_dimension_gateway.gba','ebfbb4a296a730735526612fe64105ebbf4c5a6a'),
 ('phase26_bubbles',ROOT/'patch_output/DBZ_LOG4_phase26_bubbles_start_gateway.gba','3aa4a54f95dd218f7494ea54def741883a6a8c7e'),
]
JSONS=[
 ROOT/'additive_content/playability/canonical_line.json',
 ROOT/'additive_content/gateway/postgame_dimension_gateway.json',
 ROOT/'additive_content/gateway/bubbles_start_gateway_contract.json',
 ROOT/'additive_content/gateway/phase26_bubbles_start_gateway_manifest.json',
 ROOT/'additive_content/release/v0_1_bubbles_gateway_manifest.json',
 ROOT/'additive_content/final_asset_kit/phase28_missing_asset_kit_manifest.json',
]
FILES=[
 (ROOT/'patch_output/LOG4_v0_1_bubbles_gateway_test_pack.zip','023fc9f3e5ceacbc77e6e1781792ae0bded7092c'),
 (ROOT/'patch_output/LOG4_phase28_missing_asset_kit.zip','670d4cbe2415ef387dce0c75f908d03a41834541'),
]
def sha1(p): return hashlib.sha1(p.read_bytes()).hexdigest()
def hchk(d): return (-0x19-sum(d[0xA0:0xBD]))&0xff
def main():
 errors=[]; lines=['# Project doctor report','']
 if not BASE.exists() or sha1(BASE)!=BASE_SHA1: errors.append('Base ROM missing or SHA-1 mismatch')
 for name,p,expected in ROMS:
  if not p.exists(): errors.append(f'Missing {p}'); continue
  got=sha1(p); data=p.read_bytes(); header_ok=data[0xBD]==hchk(data)
  lines.append(f'- {name}: sha1 `{got}` header_ok={header_ok} size={len(data)}')
  if got!=expected or not header_ok or len(data)>32*1024*1024: errors.append(f'{name} failed checks')
 for p,expected in FILES:
  if not p.exists(): errors.append(f'Missing {p}'); continue
  got=sha1(p); lines.append(f'- {p.relative_to(ROOT)}: sha1 `{got}`')
  if got!=expected: errors.append(f'{p.relative_to(ROOT)} SHA mismatch')
 for p in JSONS:
  if not p.exists(): errors.append(f'Missing JSON {p.relative_to(ROOT)}'); continue
  try: json.loads(p.read_text(encoding='utf-8'))
  except Exception as e: errors.append(f'Invalid JSON {p.relative_to(ROOT)}: {e}')
 lines += ['',f'Errors: {len(errors)}']
 if errors: lines += ['','## Errors',*['- '+e for e in errors]]
 else: lines += ['','## Result','PASS — v0.1 Bubbles Gateway package is structurally valid.']
 REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(f'Wrote {REPORT.relative_to(ROOT)}')
 print('PASS' if not errors else 'FAIL')
 return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
