#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'rom_base/DBZ_Buus_Fury_USA.gba'
BASE_SHA1='f1c4b07554d2a3b1ad2f325307051e775ce68087'
REPORT=ROOT/'docs/PROJECT_DOCTOR_REPORT.md'
ROMS=[('phase19_gateway',ROOT/'patch_output/DBZ_LOG4_phase19_postgame_dimension_gateway.gba','ebfbb4a296a730735526612fe64105ebbf4c5a6a')]
JSONS=[ROOT/'additive_content/playability/canonical_line.json',ROOT/'additive_content/gateway/postgame_dimension_gateway.json',ROOT/'additive_content/gateway/gateway_flags.json',ROOT/'additive_content/gateway/log_dimensions_profile.json',ROOT/'additive_content/gateway/postgame_dimension_gateway_payload_manifest.json']
def sha1(p): return hashlib.sha1(p.read_bytes()).hexdigest()
def hchk(d): return (-0x19-sum(d[0xA0:0xBD]))&0xff
def main():
 errors=[]; lines=['# Project doctor report','']
 if not BASE.exists() or sha1(BASE)!=BASE_SHA1: errors.append('Base ROM missing or SHA-1 mismatch')
 for name,p,expected in ROMS:
  if not p.exists(): errors.append(f'Missing {p}'); continue
  got=sha1(p); data=p.read_bytes(); ok=got==expected and data[0xBD]==hchk(data) and len(data)<=32*1024*1024
  lines.append(f'- {name}: sha1 `{got}` header_ok={data[0xBD]==hchk(data)} size={len(data)}')
  if not ok: errors.append(f'{name} failed checks')
 for p in JSONS:
  if not p.exists(): errors.append(f'Missing JSON {p.relative_to(ROOT)}'); continue
  try: json.loads(p.read_text(encoding='utf-8'))
  except Exception as e: errors.append(f'Invalid JSON {p.relative_to(ROOT)}: {e}')
 lines += ['',f'Errors: {len(errors)}']
 if errors: lines += ['','## Errors',*['- '+e for e in errors]]
 else: lines += ['','## Result','PASS — phase19 gateway build and contracts are structurally valid.']
 REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(f'Wrote {REPORT.relative_to(ROOT)}')
 print('PASS' if not errors else 'FAIL')
 return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
