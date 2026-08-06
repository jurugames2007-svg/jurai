#!/usr/bin/env python3
"""Phase 36: save/flag map draft.

Creates a deterministic flag allocation table. This is not written to SRAM yet;
it is the map to use once save structure hooks are verified.
"""
from __future__ import annotations
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'additive_content/phase36_save_flags'; DOC=ROOT/'docs/PHASE36_SAVE_FLAG_MAP.md'
FLAGS=['STORY_KID_BUU_DEFEATED','LOG4_POSTGAME_GATEWAY_UNLOCKED','LOG4_DEBUG_GATEWAY_UNLOCKED','LOG4_ROUTE_SUPER_UNLOCKED','LOG4_ROUTE_GT_UNLOCKED','LOG4_ROUTE_AF_UNLOCKED','DIM_LOG1_UNLOCKED','DIM_LOG2_UNLOCKED','DIM_LOG1_ENTERED','DIM_LOG2_ENTERED','LOG2_ANDROID_SIGNAL_FOUND','LOG2_CELL_JR_DEFEATED','LOG2_MINI_ROUTE_COMPLETE','ASSET_BANK_READY','GATEWAY_MENU_UNLOCKED','BUBBLES_GATE_TESTED']
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 rows=[]
 for i,f in enumerate(FLAGS): rows.append({'flag':f,'byte_index':i//8,'bit_index':i%8,'mask':f'0x{1<<(i%8):02X}','status':'reserved_not_written_to_sram'})
 csvp=OUT/'log4_save_flag_allocation.csv'
 with csvp.open('w',newline='',encoding='utf-8') as fp:
  w=csv.DictWriter(fp,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
 js={'schema':'jurai.phase36.save_flag_map.v1','policy':'allocation_only_no_sram_write','byte_count':(len(FLAGS)+7)//8,'flags':rows,'next':'verify save block before writing'}
 jp=OUT/'log4_save_flag_allocation.json'; jp.write_text(json.dumps(js,indent=2)+'\n',encoding='utf-8')
 DOC.write_text(f"# Phase 36 — Save/flag map\n\nReserved {len(FLAGS)} flags in {(len(FLAGS)+7)//8} bytes.\n\nCSV: `{csvp.relative_to(ROOT)}`\n\nJSON: `{jp.relative_to(ROOT)}`\n\nNo SRAM writes are performed yet.\n",encoding='utf-8')
 print(f'Wrote {jp}')
if __name__=='__main__': main()
