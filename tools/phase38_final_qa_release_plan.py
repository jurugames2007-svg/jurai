#!/usr/bin/env python3
"""Phase 38: QA/release plan and candidate package."""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'additive_content/phase38_release'; DOC=ROOT/'docs/PHASE38_FINAL_QA_RELEASE_PLAN.md'; ZIP=ROOT/'patch_output/LOG4_phase38_release_candidate_docs.zip'
CHECKS=['Boot in mGBA','Header checksum valid','Original-first path unchanged','Bubbles Gateway debug visible','Gateway interaction hook tested','LOG2 mini-route complete','Save/load after gateway','No crash on map transitions','IPS/BPS package excludes base ROM for public release']
FILES=[ROOT/'docs/PROJECT_PHASES_REMAINING.md',ROOT/'docs/PHASE29_TO_33_BATCH_REPORT.md',ROOT/'docs/PROJECT_DOCTOR_REPORT.md',ROOT/'docs/PHASE38_FINAL_QA_RELEASE_PLAN.md']
def sha1(p): return hashlib.sha1(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 plan={'schema':'jurai.phase38.qa_release_plan.v1','checks':[{'check':c,'status':'pending' if c not in ['Header checksum valid'] else 'passing_structural'} for c in CHECKS],'release_rule':'public release must ship patches/docs only, not base ROM'}
 jp=OUT/'phase38_qa_release_plan.json'; jp.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
 DOC.write_text('# Phase 38 — Final QA/release plan\n\n'+'\n'.join(f"- {c}" for c in CHECKS)+'\n',encoding='utf-8')
 with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.write(jp,jp.relative_to(ROOT).as_posix())
  for f in FILES:
   if f.exists(): z.write(f,f.relative_to(ROOT).as_posix())
 manifest={'schema':'jurai.phase38.release_candidate_docs.v1','zip':ZIP.relative_to(ROOT).as_posix(),'zip_sha1':sha1(ZIP),'qa_plan':jp.relative_to(ROOT).as_posix()}
 (OUT/'phase38_release_candidate_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print(f'Wrote {ZIP} {sha1(ZIP)}')
if __name__=='__main__': main()
