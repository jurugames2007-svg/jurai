#!/usr/bin/env python3
from __future__ import annotations
import csv
from pathlib import Path
from PIL import Image, ImageChops
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'playtest_output/phase20_original'
B=ROOT/'playtest_output/phase20_gateway_menu'
OUT=ROOT/'playtest_output/phase20_original_compare.csv'
DOC=ROOT/'docs/PHASE20_RUNTIME_COMPARE.md'
def changed(a,b):
 ia=Image.open(a).convert('RGBA'); ib=Image.open(b).convert('RGBA'); diff=ImageChops.difference(ia,ib)
 return 0 if diff.getbbox() is None else sum(1 for p in diff.getdata() if p!=(0,0,0,0))
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 rows=[]
 for p in sorted(A.glob('screenshot-*.png')):
  q=B/p.name
  if q.exists(): rows.append({'original':p.relative_to(ROOT).as_posix(),'phase20':q.relative_to(ROOT).as_posix(),'changed_pixels':changed(p,q)})
 with OUT.open('w',newline='',encoding='utf-8') as fp:
  w=csv.DictWriter(fp,fieldnames=['original','phase20','changed_pixels']); w.writeheader(); w.writerows(rows)
 diffs=sum(1 for r in rows if r['changed_pixels'])
 DOC.write_text(f"# Phase 20 runtime compare\n\nCompared screenshots: {len(rows)}\nScreenshots with changes: {diffs}\n\nCSV: `{OUT.relative_to(ROOT)}`\n\n"+("PASS — early original experience is preserved pixel-for-pixel.\n" if diffs==0 else "Differences detected.\n"),encoding='utf-8')
 print(f'Wrote {OUT.relative_to(ROOT)}')
 print(f'Wrote {DOC.relative_to(ROOT)}')
if __name__=='__main__': main()
