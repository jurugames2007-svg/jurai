#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'rom_base/DBZ_Buus_Fury_USA.gba'
BASE_SHA1='f1c4b07554d2a3b1ad2f325307051e775ce68087'
REPORT=ROOT/'docs/PROJECT_DOCTOR_REPORT.md'
ROMS=[
 ('phase19_gateway',ROOT/'patch_output/DBZ_LOG4_phase19_postgame_dimension_gateway.gba','ebfbb4a296a730735526612fe64105ebbf4c5a6a'),
 ('phase26_bubbles',ROOT/'patch_output/DBZ_LOG4_phase26_bubbles_start_gateway.gba','3aa4a54f95dd218f7494ea54def741883a6a8c7e'),
 ('phase30_asset_bank',ROOT/'patch_output/DBZ_LOG4_phase30_reviewed_asset_bank.gba','850f23e8db1524fa224e9cc27534e4d6662d44a3'),
 ('phase31_gateway_interaction',ROOT/'patch_output/DBZ_LOG4_phase31_gateway_interaction_payload.gba','ab593510d1cef6dcf051e478eb265330eefa3c1a'),
 ('phase32_first_route',ROOT/'patch_output/DBZ_LOG4_phase32_first_playable_route_package.gba','d70c1143fdf5a128e3afb54edaab69595b18bf20'),
 ('phase33_route_matrix',ROOT/'patch_output/DBZ_LOG4_phase33_full_route_expansion_matrix.gba','14eb4cda97292e7536b7ff3088562564b6c4e910'),
 ('phase34_hook_research',ROOT/'patch_output/DBZ_LOG4_phase34_gateway_hook_research.gba','b0b374ac455a48e19a60e3296dfbd48defb4f6fc'),
 ('phase40_hook_blueprint',ROOT/'patch_output/DBZ_LOG4_phase40_gateway_hook_blueprint.gba','bf5acf1d625d4fd24ba0e8dc177505a1e2006a6c'),
 ('phase44_title_payload',ROOT/'patch_output/DBZ_LOG4_phase44_title_screen_payload.gba','515d36faccc6b51077f083771fc056177c325ae1'),
 ('phase45_bubbles_dialogue',ROOT/'patch_output/DBZ_LOG4_phase45_bubbles_dialogue_text_hook.gba','7d6416c4934904c7ff318685df0cb6e381c91e20'),
 ('phase46_title_runtime_probe',ROOT/'patch_output/DBZ_LOG4_phase46_title_screen_runtime_hook.gba','90b56a0ba388d2975012b53ce424996d2a70fcbc'),
 ('phase47_title_kind0',ROOT/'patch_output/DBZ_LOG4_phase47_title_screen_kind0_hook.gba','81a00e341197a7d4b4158a37a4c34c2009681966'),
 ('phase48_unified_gateway',ROOT/'patch_output/DBZ_LOG4_phase48_unified_gateway_test.gba','7decb822ea9a11dfc674f890067fd2465e9c9b42'),
 ('phase49_boot_gateway',ROOT/'patch_output/DBZ_LOG4_phase49_boot_gateway_menu.gba','05823a9e846a14777121e9bee5254c0e1731f401'),
 ('phase51_boot_gateway_warp_rooms',ROOT/'patch_output/DBZ_LOG4_phase51_boot_gateway_warp_rooms.gba','f16c4b450afcab9205dd2410ee7e02ba11bab010'),
 ('phase53_native_map_trace',ROOT/'patch_output/DBZ_LOG4_phase53_native_map_findarea_trace.gba','6c90b221878bef39ff125f9a07c685e1c1da8895'),
 ('phase54_native_map_registry',ROOT/'patch_output/DBZ_LOG4_phase54_gateway_native_map_registry.gba','c2e76758af2cd989485e1b74de668c295cb88101'),
 ('phase61_dlc_asset_bank_payload',ROOT/'patch_output/DBZ_LOG4_phase61_dlc_asset_bank_payload.gba','3495fab96e7df9387f8fbd0fc854163f32be6254'),
 ('phase69_dlc_runtime_hooks',ROOT/'patch_output/DBZ_LOG4_phase69_dlc_runtime_hooks.gba','8ddc84c0a95a1316441a4066da8a2024afe7cdf5'),
]
JSONS=[
 ROOT/'additive_content/playability/canonical_line.json',
 ROOT/'additive_content/gateway/postgame_dimension_gateway.json',
 ROOT/'additive_content/gateway/bubbles_start_gateway_contract.json',
 ROOT/'additive_content/final_asset_kit/phase28_missing_asset_kit_manifest.json',
 ROOT/'additive_content/phase29_review/phase29_asset_review_seed_manifest.json',
 ROOT/'additive_content/phase30_native_bank/phase30_reviewed_asset_bank_manifest.json',
 ROOT/'additive_content/phase31_gateway_interaction/gateway_interaction_contract.json',
 ROOT/'additive_content/phase32_first_route/log2_first_route_contract.json',
 ROOT/'additive_content/phase33_route_matrix/full_route_expansion_matrix.json',
 ROOT/'additive_content/phase34_gateway_hook_research/gateway_hook_research.json',
 ROOT/'additive_content/phase39_dialogue_trace/dialogue_trace_findings.json',
 ROOT/'additive_content/phase40_gateway_hook_blueprint/gateway_hook_blueprint.json',
 ROOT/'additive_content/phase41_trace_validation/trace_validation_report.json',
 ROOT/'additive_content/phase42_readiness/v0_2_readiness_manifest.json',
 ROOT/'additive_content/phase43_next_engineering/v0_2_next_engineering_plan.json',
 ROOT/'additive_content/title_screen/phase44_title_screen_manifest.json',
 ROOT/'additive_content/title_screen/phase44_title_payload_manifest.json',
 ROOT/'additive_content/phase45_dialogue_text_hook/phase45_bubbles_dialogue_text_hook_manifest.json',
 ROOT/'additive_content/title_screen/phase46_title_screen_runtime_hook_manifest.json',
 ROOT/'additive_content/title_screen/phase47_title_screen_kind0_hook_manifest.json',
 ROOT/'additive_content/phase48_unified_gateway/phase48_unified_gateway_manifest.json',
 ROOT/'additive_content/gateway/phase49_boot_gateway_menu_manifest.json',
 ROOT/'additive_content/gateway_warp_rooms/phase51_boot_gateway_warp_rooms_manifest.json',
 ROOT/'additive_content/release/v0_3_playable_warp_rooms_manifest.json',
 ROOT/'additive_content/phase53_native_map_trace/phase53_native_map_findarea_trace_manifest.json',
 ROOT/'additive_content/phase53_native_map_trace/phase53_runtime_trace_report.json',
 ROOT/'additive_content/phase54_native_map_registry/phase54_gateway_native_map_registry_manifest.json',
 ROOT/'additive_content/release/v0_3_1_native_registry_manifest.json',
 ROOT/'additive_content/phase56_dlc_asset_audit/phase56_dlc_asset_audit.json',
 ROOT/'additive_content/phase57_playable_32x32_sprites/phase57_playable_32x32_sprites_manifest.json',
 ROOT/'additive_content/phase58_ai_portraits/phase58_ai_portraits_manifest.json',
 ROOT/'additive_content/phase59_enemy_32x32_sprites/phase59_enemy_32x32_sprites_manifest.json',
 ROOT/'additive_content/phase60_dlc_objects_tiles/phase60_dlc_objects_tiles_manifest.json',
 ROOT/'additive_content/phase61_dlc_asset_bank/phase61_dlc_asset_bank_payload_manifest.json',
 ROOT/'additive_content/phase61_dlc_asset_bank/log4_phase61_asset_bank_manifest.json',
 ROOT/'additive_content/phase61_dlc_asset_bank/phase61_runtime_report.json',
 ROOT/'additive_content/phase62_dlc_readiness_pack/phase62_dlc_readiness_contract.json',
 ROOT/'additive_content/phase62_dlc_readiness_pack/phase62_dlc_readiness_pack_manifest.json',
 ROOT/'additive_content/phase63_dlc_hook_bindings/phase63_dlc_hook_bindings.json',
 ROOT/'additive_content/phase64_runtime_sprite_enemy_hook/phase64_runtime_sprite_enemy_hook_manifest.json',
 ROOT/'additive_content/phase65_runtime_portrait_icon_hook/phase65_runtime_portrait_icon_hook_manifest.json',
 ROOT/'additive_content/phase66_native_lookup_bridge_hook/phase66_native_lookup_bridge_hook_manifest.json',
 ROOT/'additive_content/phase67_route_state_ewram_hook/phase67_route_state_ewram_hook_manifest.json',
 ROOT/'additive_content/phase68_dlc_room_ui_hook/phase68_dlc_room_ui_hook_manifest.json',
 ROOT/'additive_content/phase69_dlc_runtime_hooks_rom/phase69_dlc_runtime_hooks_rom_manifest.json',
 ROOT/'additive_content/phase70_dlc_runtime_validation/phase70_dlc_runtime_validation_report.json',
 ROOT/'additive_content/phase71_v05_dlc_runtime_hooks_pack/phase71_v05_dlc_runtime_hooks_pack_manifest.json',
 ROOT/'additive_content/phase72_hook_doctor/phase72_hook_doctor_note.json',
]
FILES=[
 (ROOT/'patch_output/LOG4_v0_1_bubbles_gateway_test_pack.zip','023fc9f3e5ceacbc77e6e1781792ae0bded7092c'),
 (ROOT/'patch_output/LOG4_phase28_missing_asset_kit.zip','670d4cbe2415ef387dce0c75f908d03a41834541'),
 (ROOT/'patch_output/LOG4_phase38_release_candidate_docs.zip','dae4f67542818a820da998602e0a7d63f6a87adb'),
 (ROOT/'patch_output/LOG4_v0_2_gateway_runtime_readiness_pack.zip','777434ba835f5c93bb2ee7c41b8411c5fd763ca0'),
 (ROOT/'patch_output/LOG4_v0_2_boot_warp_selector_pack.zip','b4ded1d1f83f4533ee06d71a7901e77473d80bd1'),
 (ROOT/'patch_output/LOG4_v0_3_playable_warp_rooms_pack.zip','731e5a8e227fa43f1bb76ddf4a7e36d8b8c1548c'),
 (ROOT/'patch_output/LOG4_v0_3_1_native_registry_pack.zip','333bdbf7251c15dc0cc65933d9fef053c111c336'),
 (ROOT/'patch_output/LOG4_v0_4_dlc_asset_readiness_pack.zip','1ab780d976373de82a8dda7a197870a32b7c2202'),
 (ROOT/'patch_output/LOG4_v0_5_dlc_runtime_hooks_pack.zip','27abc801a82ea8a140a97ad74b492dc23cbfbd82'),
]
def sha1(p): return hashlib.sha1(p.read_bytes()).hexdigest()
def hchk(d): return (-0x19-sum(d[0xA0:0xBD]))&0xff
def main():
 errors=[]; lines=['# Project doctor report','']
 if not BASE.exists() or sha1(BASE)!=BASE_SHA1: errors.append('Base ROM missing or SHA-1 mismatch')
 for name,p,expected in ROMS:
  if not p.exists(): errors.append(f'Missing {p}'); continue
  got=sha1(p); data=p.read_bytes(); header_ok=data[0xBD]==hchk(data)
  lines.append(f'- {name}: sha1 `{got}` header_ok={header_ok} size={len(data)}')
  if got!=expected or not header_ok or len(data)>32*1024*1024: errors.append(f'{name} failed checks')
 for p,expected in FILES:
  if not p.exists(): errors.append(f'Missing {p}'); continue
  got=sha1(p); lines.append(f'- {p.relative_to(ROOT)}: sha1 `{got}`')
  if got!=expected: errors.append(f'{p.relative_to(ROOT)} SHA mismatch')
 for p in JSONS:
  if not p.exists(): errors.append(f'Missing JSON {p.relative_to(ROOT)}'); continue
  try: json.loads(p.read_text(encoding='utf-8'))
  except Exception as e: errors.append(f'Invalid JSON {p.relative_to(ROOT)}: {e}')
 lines += ['',f'Errors: {len(errors)}']
 if errors: lines += ['','## Errors',*['- '+e for e in errors]]
 else: lines += ['','## Result','PASS — phase 72 DLC runtime-hooks package is structurally valid.']
 REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(f'Wrote {REPORT.relative_to(ROOT)}')
 print('PASS' if not errors else 'FAIL')
 return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
