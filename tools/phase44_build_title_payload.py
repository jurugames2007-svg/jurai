#!/usr/bin/env python3
"""Build append-only title/menu payload for the LOG4 title screen assets."""
from __future__ import annotations
import hashlib, io, json, struct, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'rom_base/DBZ_Buus_Fury_USA.gba'; BASE_SHA1='f1c4b07554d2a3b1ad2f325307051e775ce68087'
OUT_PREFIX=ROOT/'patch_output/DBZ_LOG4_phase44_title_screen_payload'
MANIFEST=ROOT/'additive_content/title_screen/phase44_title_payload_manifest.json'
DOC=ROOT/'docs/PHASE44_TITLE_PAYLOAD.md'
MAGIC=b'LOG4T44!'; VERSION=1
FILES=[ROOT/'additive_content/title_screen/LOG4_title_screen_240x160.png',ROOT/'additive_content/title_screen/LOG4_main_menu_240x160.png',ROOT/'additive_content/title_screen/LOG4_title_background_240x160.png',ROOT/'additive_content/title_screen/phase44_title_screen_manifest.json',ROOT/'include/log4_title_screen.h']
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
def sha1(p): return hashlib.sha1(p.read_bytes()).hexdigest()
def main():
 base=BASE.read_bytes()
 if hashlib.sha1(base).hexdigest()!=BASE_SHA1: raise SystemExit('Base SHA-1 mismatch')
 bio=io.BytesIO()
 entries=[]
 with zipfile.ZipFile(bio,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for f in FILES:
   if f.exists():
    z.write(f,f.relative_to(ROOT).as_posix()); entries.append({'file':f.relative_to(ROOT).as_posix(),'sha1':sha1(f),'size':f.stat().st_size})
 payload=bio.getvalue(); directory=json.dumps({'schema':'jurai.phase44.title_payload.v1','files':entries,'payload_sha1':hashlib.sha1(payload).hexdigest()},separators=(',',':')).encode()
 header=MAGIC+struct.pack('<III',VERSION,len(directory),len(payload)); final=bytearray(base+header+directory+payload)
 while len(final)%4: final.append(0)
 final=bytes(final); gba=OUT_PREFIX.with_suffix('.gba'); ips=OUT_PREFIX.with_suffix('.ips'); txt=OUT_PREFIX.with_suffix('.txt')
 gba.write_bytes(final); ips.write_bytes(ips_patch(base,final))
 manifest={'schema':'jurai.phase44.title_payload_build.v1','output_gba':gba.relative_to(ROOT).as_posix(),'output_ips':ips.relative_to(ROOT).as_posix(),'modified_sha1':hashlib.sha1(final).hexdigest(),'entries':entries}
 MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 DOC.write_text(f"# Phase 44 — Title screen payload\n\nAppend-only ROM payload containing the LOG4 title/menu art.\n\nOutput ROM: `{gba.relative_to(ROOT)}`\n\nModified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n\nManifest: `{MANIFEST.relative_to(ROOT)}`\n",encoding='utf-8')
 txt.write_text(DOC.read_text(encoding='utf-8'),encoding='utf-8')
 print(f'Wrote {gba}')
if __name__=='__main__': main()
