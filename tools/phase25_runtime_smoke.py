#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'playtest_output/phase25_variants'
DOC=ROOT/'docs/PHASE25_RUNTIME_SMOKE.md'
MANIFEST=ROOT/'additive_content/gateway/phase25_snakeway_npc_variant_matrix_manifest.json'

def contact(variant_dir: Path):
    files=sorted(variant_dir.glob('screenshot-*.png'))
    if not files: return None
    thumbs=[]
    for f in files:
        thumbs.append((f.name,Image.open(f).convert('RGBA').resize((120,80),Image.Resampling.NEAREST)))
    w=4*170; h=((len(thumbs)+3)//4)*110
    sheet=Image.new('RGBA',(w,h),(20,20,28,255)); d=ImageDraw.Draw(sheet)
    for i,(label,img) in enumerate(thumbs):
        x=(i%4)*170; y=(i//4)*110
        sheet.alpha_composite(img,(x,y+20)); d.text((x,y+2),label,fill=(255,255,255,255))
    p=variant_dir.with_name(variant_dir.name+'_contact.png'); sheet.save(p); return p

def main():
    data=json.loads(MANIFEST.read_text(encoding='utf-8'))
    rows=[]
    for v in data['variants']:
        d=OUT/v['id']; rp=d/'skip-playtest-result.json'
        status='missing'
        if rp.exists(): status=json.loads(rp.read_text()).get('status','unknown')
        cp=contact(d) if d.exists() else None
        rows.append({'id':v['id'],'rom':v['output_gba'],'sha1':v['modified_sha1'],'status':status,'contact':cp.relative_to(ROOT).as_posix() if cp else ''})
    lines=['# Phase 25 runtime smoke','', 'Automated boot/input smoke for Snakeway NPC variant matrix.','']
    for r in rows:
        lines.append(f"- `{r['id']}` status=`{r['status']}` sha1=`{r['sha1']}` contact=`{r['contact']}`")
    DOC.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Wrote {DOC.relative_to(ROOT)}')
if __name__=='__main__': main()
