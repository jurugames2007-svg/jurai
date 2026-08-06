#!/usr/bin/env python3
"""Phase 37: content insertion manifest."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'additive_content/phase37_insertion'; DOC=ROOT/'docs/PHASE37_CONTENT_INSERTION_MANIFEST.md'
STAGES=[
 {'stage':1,'name':'Gateway UI/text','inputs':['phase31 gateway interaction payload'],'gate':'native text/menu hook verified'},
 {'stage':2,'name':'LOG2 mini-route maps/items','inputs':['phase32 route package','phase30 asset bank'],'gate':'map transition + item record verified'},
 {'stage':3,'name':'LOG2 enemies','inputs':['CELL_JR','ANDROID_17_BOSS'],'gate':'enemy spawn record verified'},
 {'stage':4,'name':'GT Black Star intro','inputs':['BLACK_STAR_RADAR','BLACK_STAR_1','GENERAL_RILDO'],'gate':'LOG2 mini-route stable'},
 {'stage':5,'name':'Super route opener','inputs':['BEERUS_PLANET','BEERUS','SSG icons'],'gate':'Gateway stable'},
 {'stage':6,'name':'AF branch opener','inputs':['AF_KAIOSHIN_REALM','XICOR_AF','IKL_AF'],'gate':'Super/GT route opener stable'},
]
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 data={'schema':'jurai.phase37.content_insertion_manifest.v1','policy':'insert in small reversible batches','stages':STAGES}
 jp=OUT/'content_insertion_order.json'; jp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 lines=['# Phase 37 — Content insertion manifest','','Insertion order for turning data/assets into gameplay.','']
 for s in STAGES: lines.append(f"{s['stage']}. **{s['name']}** — gate: {s['gate']}")
 DOC.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(f'Wrote {jp}')
if __name__=='__main__': main()
