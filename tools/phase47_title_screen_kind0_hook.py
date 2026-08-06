#!/usr/bin/env python3
"""Phase 47: try a kind-0 uncompressed title/splash hook.

Phase 46 used a synthetic compressed stream that passed DragonByteZ but did not
render correctly in the game's title flow. This safer probe appends a kind-0
Webfoot container (raw copy) with the LOG4 title index data and redirects the
same title/splash pointers.
"""
from __future__ import annotations
import hashlib, json, struct
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'rom_base/DBZ_Buus_Fury_USA.gba'; BASE_SHA1='f1c4b07554d2a3b1ad2f325307051e775ce68087'
TITLE=ROOT/'additive_content/title_screen/LOG4_title_screen_240x160.png'
BG_PAL=ROOT/'tools/buusfury_disassembly/assets/palettes/bg.pal'
OUT_PREFIX=ROOT/'patch_output/DBZ_LOG4_phase47_title_screen_kind0_hook'
MANIFEST=ROOT/'additive_content/title_screen/phase47_title_screen_kind0_hook_manifest.json'
DOC=ROOT/'docs/PHASE47_TITLE_SCREEN_KIND0_HOOK.md'
OLD=0x083BE3D4; REFS=[0x5414,0x1E744,0x1E9E0]
W,H=240,160

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
def read_u32(d,o): return struct.unpack_from('<I',d,o)[0]
def write_u32(d,o,v): struct.pack_into('<I',d,o,v)
def align(v,b): return (v+b-1)&~(b-1)
def hchk(d): return (-0x19-sum(d[0xA0:0xBD]))&0xff
def pal():
 raw=BG_PAL.read_bytes(); out=[]
 for i in range(0,512,2):
  v=raw[i]|raw[i+1]<<8; r=v&31; g=(v>>5)&31; b=(v>>10)&31
  out.append(((r<<3)|(r>>2),(g<<3)|(g>>2),(b<<3)|(b>>2)))
 return out
def nearest(c,p):
 r,g,b=c; best=0; bd=10**9
 for i,(pr,pg,pb) in enumerate(p):
  dd=(r-pr)**2+(g-pg)**2+(b-pb)**2
  if dd<bd: best=i; bd=dd
 return best
def raw_indices():
 p=pal(); im=Image.open(TITLE).convert('RGB').resize((W,H),Image.Resampling.NEAREST)
 return bytes(nearest(px,p) for px in im.getdata())
def main():
 base=BASE.read_bytes()
 if hashlib.sha1(base).hexdigest()!=BASE_SHA1: raise SystemExit('base mismatch')
 for ref in REFS:
  if read_u32(base,ref)!=OLD: raise SystemExit(f'precondition fail {ref:x}')
 raw=raw_indices(); container=struct.pack('<II',0,len(raw))+raw
 mod=bytearray(base); off=align(len(mod),4); mod.extend(b'\xff'*(off-len(mod))); va=0x08000000+off; mod.extend(container)
 for ref in REFS: write_u32(mod,ref,va)
 mod[0xA0:0xAC]=b'LOG4TITLE47\0'; mod[0xBD]=hchk(mod)
 while len(mod)%4: mod.append(0)
 final=bytes(mod); gba=OUT_PREFIX.with_suffix('.gba'); ips=OUT_PREFIX.with_suffix('.ips'); txt=OUT_PREFIX.with_suffix('.txt')
 gba.write_bytes(final); ips.write_bytes(ips_patch(base,final))
 manifest={'schema':'jurai.phase47.title_kind0_hook.v1','output_gba':gba.relative_to(ROOT).as_posix(),'output_ips':ips.relative_to(ROOT).as_posix(),'modified_sha1':hashlib.sha1(final).hexdigest(),'new_va':f'0x{va:08X}','container_offset':f'0x{off:06X}','kind':0,'size':len(raw)}
 MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 DOC.write_text(f"# Phase 47 — Title screen kind-0 hook\n\nOutput ROM: `{gba.relative_to(ROOT)}`\n\nModified SHA-1: `{hashlib.sha1(final).hexdigest()}`\n\nNew VA: `0x{va:08X}`\n\nThis probes whether the title flow accepts an uncompressed kind-0 container.\n",encoding='utf-8')
 txt.write_text(DOC.read_text(encoding='utf-8'),encoding='utf-8')
 print(gba)
if __name__=='__main__': main()
