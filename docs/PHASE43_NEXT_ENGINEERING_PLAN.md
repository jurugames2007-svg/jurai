# Phase 43 — Next engineering plan

Milestone: **v0.2 Gateway Runtime**

## Ordered tasks

- **43A** — Use watchpoint PCs 0x03000268 and 0x03000060 to trace caller registers/source pointer -> caller register trace JSON
- **43B** — Locate compressed dialogue package for first Other World/Bubbles text -> ROM offset + decompression validation
- **43C** — Patch data pointer or package to Gateway text bank with fallback -> ROM that changes one existing Bubbles dialogue safely
- **43D** — Reuse native list/menu flow or simple dialogue branch for Super/GT/AF/LOG1/LOG2 choices -> interactive gateway prototype
- **43E** — Route LOG2 option to first route contract -> first route transition smoke test

## Success criteria

- Talk to Bubbles/Gate Guide
- See selectable gateway choices
- Select LOG2
- Land in safe map or route stub
- Return without crash

Plan JSON: `additive_content/phase43_next_engineering/v0_2_next_engineering_plan.json`
