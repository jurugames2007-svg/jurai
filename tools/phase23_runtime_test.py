#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'playtest_output/phase23_snakeway_npc'
CONTACT=ROOT/'playtest_output/phase23_snakeway_npc_contact.png'
DOC=ROOT/'docs/PHASE23_SNAKEWAY_NPC_RUNTIME.md'
def main():
 files=sorted(FOLDER.glob('screenshot-*.png'))
 if files:
  thumbs=[]
  for f in files:
   thumbs.append((f.name,Image.open(f).convert('RGBA').resize((120,80),Image.Resampling.NEAREST)))
  w=4*170; h=((len(thumbs)+3)//4)*110
  sheet=Image.new('RGBA',(w,h),(20,20,28,255)); d=ImageDraw.Draw(sheet)
  for i,(label,img) in enumerate(thumbs):
   x=(i%4)*170; y=(i//4)*110; sheet.alpha_composite(img,(x,y+20)); d.text((x,y+2),label,fill=(255,255,255,255))
  sheet.save(CONTACT)
 rp=FOLDER/'skip-playtest-result.json'
 result=json.loads(rp.read_text()) if rp.exists() else {'status':'missing'}
 DOC.write_text(f"# Phase 23 Snakeway NPC runtime\n\nStatus: `{result.get('status')}`\n\nContact sheet: `{CONTACT.relative_to(ROOT) if CONTACT.exists() else 'missing'}`\n\nResult: `{rp.relative_to(ROOT) if rp.exists() else 'missing'}`\n\nThis only confirms automated boot/input stability; visual/manual testing is needed to confirm the NPC appears and is interactable.\n",encoding='utf-8')
 print(f'Wrote {DOC.relative_to(ROOT)}')
if __name__=='__main__': main()
