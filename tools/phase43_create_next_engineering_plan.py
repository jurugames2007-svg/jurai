#!/usr/bin/env python3
"""Phase 43: final next engineering plan for v0.2."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'additive_content/phase43_next_engineering'
DOC=ROOT/'docs/PHASE43_NEXT_ENGINEERING_PLAN.md'
PLAN={
 'schema':'jurai.phase43.next_engineering_plan.v1',
 'milestone':'v0.2 Gateway Runtime',
 'blocking_problem':'Need native script/menu hook so Bubbles opens a real gateway menu.',
 'ordered_tasks':[
  {'id':'43A','task':'Use watchpoint PCs 0x03000268 and 0x03000060 to trace caller registers/source pointer','deliverable':'caller register trace JSON'},
  {'id':'43B','task':'Locate compressed dialogue package for first Other World/Bubbles text','deliverable':'ROM offset + decompression validation'},
  {'id':'43C','task':'Patch data pointer or package to Gateway text bank with fallback','deliverable':'ROM that changes one existing Bubbles dialogue safely'},
  {'id':'43D','task':'Reuse native list/menu flow or simple dialogue branch for Super/GT/AF/LOG1/LOG2 choices','deliverable':'interactive gateway prototype'},
  {'id':'43E','task':'Route LOG2 option to first route contract','deliverable':'first route transition smoke test'},
 ],
 'success_criteria':['Talk to Bubbles/Gate Guide','See selectable gateway choices','Select LOG2','Land in safe map or route stub','Return without crash'],
 'fallbacks':['phase26 text debug build','phase31 data payload','phase32 first route data package'],
}
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 jp=OUT/'v0_2_next_engineering_plan.json'; jp.write_text(json.dumps(PLAN,indent=2)+'\n',encoding='utf-8')
 lines=['# Phase 43 — Next engineering plan','','Milestone: **v0.2 Gateway Runtime**','','## Ordered tasks','']
 for t in PLAN['ordered_tasks']: lines.append(f"- **{t['id']}** — {t['task']} -> {t['deliverable']}")
 lines += ['','## Success criteria','']+[f"- {s}" for s in PLAN['success_criteria']]+['',f"Plan JSON: `{jp.relative_to(ROOT)}`"]
 DOC.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(f'Wrote {jp}')
if __name__=='__main__': main()
