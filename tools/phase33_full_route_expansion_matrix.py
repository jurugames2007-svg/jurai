#!/usr/bin/env python3
"""Phase 33: full route expansion matrix."""
from __future__ import annotations
import hashlib, io, json, struct, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'rom_base/DBZ_Buus_Fury_USA.gba'; BASE_SHA1='f1c4b07554d2a3b1ad2f325307051e775ce68087'
OUT=ROOT/'additive_content/phase33_route_matrix'; DOC=ROOT/'docs/PHASE33_FULL_ROUTE_EXPANSION_MATRIX.md'; OUT_PREFIX=ROOT/'patch_output/DBZ_LOG4_phase33_full_route_expansion_matrix'
MAGIC=b'LOG4R33!'; VERSION=1
ROUTES={
 'SUPER_ROUTE':['BEERUS_PLANET','UNIVERSE_6_ARENA','FUTURE_CITY_RUINS','TOURNAMENT_POWER','PLANET_VAMPA','NEW_NAMEK','PLANET_CEREAL'],
 'GT_ROUTE':['PLANET_M2_FACTORY','GT_SHADOW_DRAGON_FIELD','HELL_GT','CAPSULE_RIFT_LAB'],
 'AF_ROUTE':['AF_KAIOSHIN_REALM','AF_XICOR_LAB'],
 'LOG1_DIMENSION':['LOG1_SNAKE_ROAD_MEMORY','LOG1_NAMEK_MEMORY'],
 'LOG2_DIMENSION':['LOG2_WEST_CITY_MEMORY','LOG2_CELL_GAMES_MEMORY'],
}
ENEMY_BY_ROUTE={
 'SUPER_ROUTE':['BEERUS','GOLDEN_FRIEZA','HIT','GOKU_BLACK','ZAMASU','JIREN','BROLY_DBS','MORO','GRANOLAH'],
 'GT_ROUTE':['GENERAL_RILDO','BABY_VEGETA','SUPER_17','OMEGA_SHENRON'],
 'AF_ROUTE':['IKL_AF','XICOR_FINAL'],
 'LOG1_DIMENSION':['RADITZ','NAPPA','VEGETA_SAIYAN','GINYU_FORCE','FRIEZA_LOG1','WOLF_LOG1'],
 'LOG2_DIMENSION':['ANDROID_17_BOSS','ANDROID_18_BOSS','ANDROID_19','DR_GERO','CELL_IMPERFECT','CELL_JR','CELL_PERFECT','COOLER'],
}

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
 if hashlib.sha1(base).hexdigest()!=BASE_SHA1: raise SystemExit('base mismatch')
 OUT.mkdir(parents=True,exist_ok=True)
 matrix={'schema':'jurai.phase33.full_route_matrix.v1','routes':[],'quality_gates':['assets READY_FOR_ROM_TEST_DRAFT or APPROVED','native script hooks decoded','save flags mapped','mGBA runtime pass']}
 for route,maps in ROUTES.items():
  chapters=[]
  for idx,map_id in enumerate(maps,1):
   enemies=ENEMY_BY_ROUTE[route][max(0,min(len(ENEMY_BY_ROUTE[route])-1,idx-1)):max(0,min(len(ENEMY_BY_ROUTE[route]),idx+1))]
   chapters.append({'chapter':idx,'map':map_id,'enemies':enemies,'objective':f'Complete {map_id} encounter','status':'planned_assets_exist_hooks_pending'})
  matrix['routes'].append({'route_id':route,'chapters':chapters,'completion_flag':f'{route}_COMPLETE'})
 path=OUT/'full_route_expansion_matrix.json'; path.write_text(json.dumps(matrix,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 md=OUT/'full_route_expansion_matrix.md'; lines=['# Full route expansion matrix','']
 for r in matrix['routes']:
  lines.append(f"## {r['route_id']}"); lines.append('')
  for ch in r['chapters']: lines.append(f"- Chapter {ch['chapter']}: {ch['map']} — enemies: {', '.join(ch['enemies'])}")
  lines.append('')
 md.write_text('\n'.join(lines),encoding='utf-8')
 bio=io.BytesIO()
 with zipfile.ZipFile(bio,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in [path,md]: z.write(p,p.relative_to(ROOT).as_posix())
 payload=bio.getvalue(); directory=json.dumps({'schema':'jurai.phase33.payload.v1','files':[path.relative_to(ROOT).as_posix(),md.relative_to(ROOT).as_posix()],'payload_sha1':hashlib.sha1(payload).hexdigest()},separators=(',',':')).encode()
 header=MAGIC+struct.pack('<III',VERSION,len(directory),len(payload)); final=bytearray(base+header+directory+payload)
 while len(final)%4: final.append(0)
 final=bytes(final); gba=OUT_PREFIX.with_suffix('.gba'); ips=OUT_PREFIX.with_suffix('.ips'); txt=OUT_PREFIX.with_suffix('.txt')
 gba.write_bytes(final); ips.write_bytes(ips_patch(base,final))
 manifest={'schema':'jurai.phase33.route_matrix_build.v1','output_gba':gba.relative_to(ROOT).as_posix(),'output_ips':ips.relative_to(ROOT).as_posix(),'modified_sha1':hashlib.sha1(final).hexdigest(),'matrix':path.relative_to(ROOT).as_posix()}
 (OUT/'phase33_route_matrix_build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 DOC.write_text(f"# Phase 33 — Full route expansion matrix\n\nCreated full route/chapter map for Super, GT, AF, LOG1 and LOG2.\n\nOutput ROM: `{gba.relative_to(ROOT)}`\n\nModified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n\nMatrix: `{path.relative_to(ROOT)}`\n",encoding='utf-8')
 txt.write_text(DOC.read_text(encoding='utf-8'),encoding='utf-8')
 print(f'Wrote {gba}')
if __name__=='__main__': main()
