#!/usr/bin/env python3
"""Phase 32: first playable mini-route data package.

Chooses LOG2_DIMENSION as the first route candidate because LOG2 has the largest
reference asset catalog. This is still a payload/contract until scripts are
hooked.
"""
from __future__ import annotations

import hashlib, io, json, struct, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'rom_base/DBZ_Buus_Fury_USA.gba'; BASE_SHA1='f1c4b07554d2a3b1ad2f325307051e775ce68087'
OUT=ROOT/'additive_content/phase32_first_route'; DOC=ROOT/'docs/PHASE32_FIRST_PLAYABLE_ROUTE_PACKAGE.md'
OUT_PREFIX=ROOT/'patch_output/DBZ_LOG4_phase32_first_playable_route_package'
MAGIC=b'LOG4R32!'; VERSION=1

def ips_patch(o,m):
 out=bytearray(b'PATCH'); pos=0
 while pos<len(m):
  if pos<len(o) and o[pos]==m[pos]: pos+=1; continue
  start=pos; pos+=1
  while pos<len(m) and pos-start<0xffff:
   if pos<len(o) and o[pos]==m[pos]: break
   pos+=1
  chunk=m[start:pos]; out.extend(start.to_bytes(3,'big')); out.extend(len(chunk).to_bytes(2,'big')); out.extend(chunk)
 out.extend(b'EOF'); out.extend(len(m).to_bytes(3,'big')); return bytes(out)

def main():
 base=BASE.read_bytes()
 if hashlib.sha1(base).hexdigest()!=BASE_SHA1: raise SystemExit('Base mismatch')
 OUT.mkdir(parents=True,exist_ok=True)
 route={
  'schema':'jurai.phase32.first_playable_route.v1',
  'route_id':'LOG2_DIMENSION_CELL_GAMES_MEMORY_MINI_ROUTE',
  'dimension':'LOG2_DIMENSION',
  'goal':'Create first complete mini-route: gateway -> West City memory -> Android scout -> Cell Jr battle -> Cell Games memory -> return',
  'nodes':[
   {'id':'enter_gateway','type':'gateway_option','target':'LOG2_DIMENSION','sets':['DIM_LOG2_ENTERED']},
   {'id':'west_city_memory','type':'map','map':'LOG2_WEST_CITY_MEMORY','objective':'Find Capsule Corp signal'},
   {'id':'bulma_memory','type':'npc_dialogue','npc':'BULMA_MEMORY','text':'This is a LOG2 memory. Android energy is rising.'},
   {'id':'android_scout','type':'enemy','enemy':'ANDROID_17_BOSS','count':1,'sets':['LOG2_ANDROID_SIGNAL_FOUND']},
   {'id':'cell_jr_battle','type':'battle','enemy':'CELL_JR','count':3,'sets':['LOG2_CELL_JR_DEFEATED']},
   {'id':'reward','type':'item_reward','item':'TIME_CHAMBER_KEY','sets':['LOG2_MINI_ROUTE_COMPLETE']},
   {'id':'return_gate','type':'return','target':'CAPSULE_CORP_RIFT_GATEWAY'},
  ],
  'required_assets':['LOG2_WEST_CITY_MEMORY','CELL_JR','ANDROID_17_BOSS','BULMA_MEMORY','TIME_CHAMBER_KEY'],
  'status':'data_ready_script_hooks_pending'
 }
 path=OUT/'log2_first_route_contract.json'; path.write_text(json.dumps(route,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 text='Bubbles: LOG2 memory opened. Find Capsule Corp signal. Defeat Cell Jr. Return to the gate.'
 bank=OUT/'log2_first_route_text.utf16le.bin'; bank.write_bytes(text.encode('utf-16le')+b'\0\0')
 bio=io.BytesIO()
 with zipfile.ZipFile(bio,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in [path,bank]: z.write(p,p.relative_to(ROOT).as_posix())
 payload=bio.getvalue(); directory=json.dumps({'schema':'jurai.phase32.payload.v1','files':[path.relative_to(ROOT).as_posix(),bank.relative_to(ROOT).as_posix()],'payload_sha1':hashlib.sha1(payload).hexdigest()},separators=(',',':')).encode()
 header=MAGIC+struct.pack('<III',VERSION,len(directory),len(payload)); final=bytearray(base+header+directory+payload)
 while len(final)%4: final.append(0)
 final=bytes(final); gba=OUT_PREFIX.with_suffix('.gba'); ips=OUT_PREFIX.with_suffix('.ips'); txt=OUT_PREFIX.with_suffix('.txt')
 gba.write_bytes(final); ips.write_bytes(ips_patch(base,final))
 manifest={'schema':'jurai.phase32.first_route_build.v1','output_gba':gba.relative_to(ROOT).as_posix(),'output_ips':ips.relative_to(ROOT).as_posix(),'modified_sha1':hashlib.sha1(final).hexdigest(),'contract':path.relative_to(ROOT).as_posix()}
 (OUT/'phase32_first_route_build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 DOC.write_text(f"# Phase 32 — First playable route package\n\nRoute: LOG2 Cell Games Memory mini-route.\n\nOutput ROM: `{gba.relative_to(ROOT)}`\n\nModified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n\nThis is data-ready; native script hooks are pending.\n",encoding='utf-8')
 txt.write_text(DOC.read_text(encoding='utf-8'),encoding='utf-8')
 print(f'Wrote {gba}')
if __name__=='__main__': main()
