#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'playtest_output/phase22_snakeway'
DOC=ROOT/'docs/PHASE22_SNAKEWAY_GATEKEEPER_RUNTIME.md'
CONTACT=ROOT/'playtest_output/phase22_snakeway_contact.png'
def main():
 files=sorted(FOLDER.glob('screenshot-*.png'))
 if files:
  thumbs=[]
  for f in files:
   thumbs.append((f.name,Image.open(f).convert('RGBA').resize((120,80),Image.Resampling.NEAREST)))
  w=4*170; h=((len(thumbs)+3)//4)*110
  sheet=Image.new('RGBA',(w,h),(20,20,28,255)); d=ImageDraw.Draw(sheet)
  for i,(label,im) in enumerate(thumbs):
   x=(i%4)*170; y=(i//4)*110; sheet.alpha_composite(im,(x,y+20)); d.text((x,y+2),label,fill=(255,255,255,255))
  sheet.save(CONTACT)
 result_path=FOLDER/'skip-playtest-result.json'
 result=json.loads(result_path.read_text()) if result_path.exists() else {'status':'missing'}
 DOC.write_text(f"# Phase 22 Snakeway Gatekeeper runtime\n\nStatus: `{result.get('status')}`\n\nContact sheet: `{CONTACT.relative_to(ROOT) if CONTACT.exists() else 'missing'}`\n\nResult: `{result_path.relative_to(ROOT) if result_path.exists() else 'missing'}`\n",encoding='utf-8')
 print(f'Wrote {DOC.relative_to(ROOT)}')
if __name__=='__main__': main()
