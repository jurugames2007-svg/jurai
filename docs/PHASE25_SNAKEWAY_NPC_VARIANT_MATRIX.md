# Phase 25 — Snakeway NPC variant matrix

Route A: creates multiple NPC-record variants to manually identify which native entity fields control sprite visibility/interactability.

## Variants

- `v01_template65_line` — `patch_output/phase25_snakeway_variants/DBZ_LOG4_phase25_v01_template65_line.gba` — Control variant: native template 65 repeated across Snakeway. SHA-1 `21ff3e67f686e0f5ab83ad2479f0ee12e169f28d`
- `v02_template65_actor297_u16_06` — `patch_output/phase25_snakeway_variants/DBZ_LOG4_phase25_v02_template65_actor297_u16_06.gba` — Tests hypothesis: u16 @ 0x06 is actor/character id. SHA-1 `e71fd617f3ed90b455365b0a3be9f73dd2f93f51`
- `v03_template141_line` — `patch_output/phase25_snakeway_variants/DBZ_LOG4_phase25_v03_template141_line.gba` — Different native NPC template with multiple pointer-like fields. SHA-1 `1130e6486612a50dbe756bb8c2f5e6202ef0388c`
- `v04_template146_cluster` — `patch_output/phase25_snakeway_variants/DBZ_LOG4_phase25_v04_template146_cluster.gba` — Clusters a known NPC/object-like template near early Snakeway view. SHA-1 `5ee86187ff99067e0671f7d44042da81a592721d`
- `v05_template156_actor297_u16_06` — `patch_output/phase25_snakeway_variants/DBZ_LOG4_phase25_v05_template156_actor297_u16_06.gba` — Tests actor-id hypothesis on a template also seen near item-like records. SHA-1 `a1766d329016a252f5b9904ae509dd2499451535`
- `v06_template65_actor297_u16_0a` — `patch_output/phase25_snakeway_variants/DBZ_LOG4_phase25_v06_template65_actor297_u16_0a.gba` — Tests alternate u16 slot 0x0A as actor/visual field. SHA-1 `a77e607efb69f0aab446a9e6021e7f959f3ae5b2`

Manifest: `additive_content/gateway/phase25_snakeway_npc_variant_matrix_manifest.json`
