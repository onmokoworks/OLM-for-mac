# OLMRadialBlur case0010 PF8 writeback actual-AEX witness — 2026-08-05

Status: `exact`.

The actual Windows AEX Rotation owner returned from `FUN_180004640`; the gated `+0x4ec3/+0x4ec8` sampler destination, `+0x7bb0` internal cell, and native `+0x7c14/+0x7c19` PF8 store were all observed for `(1612,6)` and `(1614,6)`.

The JSON retains sampler coordinates and returned float words, internal-cell pointers, the mandatory stack destination, PF8 scale word, XMM float words, and bytes immediately before and after the native store.

Checks: `{"blur_type_is_rotation": true, "both_internal_cells_observed": true, "destination_pointer_relations": true, "exactly_two_pf8_calls_observed": true, "exactly_two_sampler_calls": true, "internal_pointer_relations": true, "native_store_matches_oracle": true, "native_store_observed": true, "rotation_owner_observed": true, "rotation_worker_returned": true, "sampler_pointer_relations": true, "sampler_return_observed": true, "sampler_to_writeback_same_cell": true, "stopped_after_final_witness": true}`.

Boundary: this closes actual-AEX CPU sampler → internal-frame → PF8-world writeback. It does not identify the provenance of the legacy white PNG or prove AE export behavior.

The post-worker/pre-PF8 Unicorn checkpoint is retained at `refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805/post_worker_pre_pf8.aexcp` with SHA-256 `47b7911d1ba4628b5c318d220ad53d06ec0819c4e8fd805d6c6d28ebf871d67a`.
