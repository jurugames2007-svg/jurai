# Phase 23 — Snakeway NPC injection probe

Experimental build that points the Snakeway map entry at a copied native NPC record.

Output ROM: `patch_output/DBZ_LOG4_phase23_snakeway_npc_probe.gba`
Modified SHA-1: `cb090a41584472d323deb4211e3926120aa6b8f4`
NPC VA: `0x08800000`
Extended map table VA: `0x08800020`

If the map crashes, entity-record semantics need more decoding before real NPC insertion.
