# OLMRadialBlur final independent semantic re-audit

Date: 2026-08-16  
Mode: read-only re-audit after the final Ghidra naming pass and canonical-master rebuild. No Ghidra or production-source mutation was made by this audit.

## Final decision: GO

The goal is complete at the defensible **behavior-level semantic classification** standard:

- frozen primary scope: **362/362 function starts**, exactly once;
- missing / extra / duplicate addresses: **0 / 0 / 0**;
- master parse gaps: **0**;
- live/master current-name equality: **362/362**;
- live duplicate names: **0**;
- named live functions: **338/362**;
- deliberate automatic-name exceptions: **24/362**, all individually bounded by Medium/Low canonical identity or by High behavior plus Medium canonical-name confidence;
- safe pure-High operation names left unapplied: **0**;
- registered callback closure: the one out-of-range function start, `0x18001ce70`, and two address-taken local labels are classified in r16.

The correct completion wording is:

> Every frozen OLMRadialBlur function start has a documented behavioral meaning, evidence, call/reference context, Mac mapping or explicit absence, and bounded confidence. Exact original C++ names are not claimed where the binary does not justify them.

Do not restate this as “all 362 original source symbols recovered.”

## Requested correction recheck

### Low-range review

- `0x180001ac0`: corrected to `degrees * π/180` plus reciprocal — PASS.
- `0x18000a9d0`: corrected to Zoom scatter in r05, master, live Ghidra, and `mac_render_mapping.md` — PASS.
- `0x180009d80`, `0x18000a850`, `0x18000a8f0`: primary rows identify their exclusive Windows Zoom owner — PASS. Cross-map references to similar Rotation arithmetic are analog mappings, not Windows ownership claims.
- `0x180001ab0`: only bare-return/no-op behavior is High; purpose remains explicitly unknown — PASS.
- r03 rename log no longer creates duplicate ledger-shaped rows — PASS.

### Mid-range review

- `0x18000f000`: parameter checkout/handle payload clone, not global data — PASS.
- all 13 direct public zero-return arms have exact `PF_Cmd` IDs, roles, jump-table evidence, High confidence, and distinct live names — PASS.
- base vtable no-op arms are resolved (`USER_CHANGED_PARAM`, base `UPDATE_PARAMS_UI`, sequence setup/setdown/resetup/flatten) — PASS.
- `0x18000c480`: no direct Mac Dynamic Stream counterpart is claimed — PASS.
- `0x18000e5f0`: both render-info and four-call `UpdateParamsUI` reachability appear in the row and r07 range summary — PASS.
- `entry_point`: described as a sparse dispatcher through ordinal `0x21`, including shared return-zero/default behavior — PASS.

### r13 review

- `0x180019200`: `ColorARGB_To_RGBA` — PASS.
- `0x180019cb0`: `GradientStops_EvaluateARGB` — PASS.
- `0x18001a190` / `0x18001a1f0`: `den/num` reciprocal scaling — PASS.
- `0x18001a310` / `0x18001a390`: checkout/checkin helpers — PASS.
- `0x180019220`: rectangle outline plus four tick pairs — PASS.
- `0x18001a060`: Mac correspondence explicitly analog-only — PASS.
- `0x1800195f0`: text-layout forwarding role with exact alignment left Medium/unresolved — PASS.

## Naming and master integrity

The final live naming snapshot contains 338 semantic names and 24 deliberate automatic names. The prior codecvt collision is fixed: `0x180015610` is `codecvt_utf8_utf16_do_length`, while `0x180016690` is `thunk_codecvt_utf8_utf16_do_length`.

The canonical master was rebuilt from the final live address/name snapshot:

- all 362 `current_name` values exactly match live Ghidra;
- name annotations/history are separated into `name_history` rather than contaminating `current_name`;
- malformed r10/r15 name fields are gone;
- duplicate current names are zero.

The 18 previously applied Medium-confidence names are explicitly accepted as conservative navigation labels in `naming_policy.md`. Their machine operation is proven; suffix/owner/typedef uncertainty is separately bounded and is not presented as recovered source spelling.

## Remaining bounded uncertainties — not blockers

The 24 automatic names are intentional, not unfinished High-confidence work:

- Low behavior/source identity: `0x180009360`, `0x180009370`, `0x18001a540`, `0x18001a550`, `0x18001a560`.
- Medium canonical identity or generic wrapper specialization: `0x18000c1b0`, `0x18000c220`, `0x18000f4c0`, `0x18000f5e0`, `0x18000ff40`, `0x1800154c0`, `0x180015f20`, `0x180016030`, `0x180019070`, `0x180019130`, `0x180019160`, `0x180019220`, `0x1800195f0`, `0x180019700`, `0x180019f20`, `0x18001a170`, `0x18001a290`, `0x18001a2a0`.
- High semantic behavior but Medium canonical name: `0x18001c3c0`.
- `0x180001ab0` has a semantic name for no-op behavior, but its source-level purpose remains explicitly unknown.

These functions all have behavioral descriptions and evidence. Renaming them further would overstate canonical identity.

## r16 callback closure

`RadialBlur_RegisterComputeCacheCallbacks@0x18000f7c0` registers four targets:

- local label `0x18001cdb0`: slot-0 forwarding operation;
- `0x18001cde0 RadialBlur_ComputeCache_CopyValue`;
- local label `0x18001ce50`: slot-`+0x10` forwarding operation;
- `0x18001ce70 RadialBlur_ComputeCache_DestroyValue`.

Exactly one callback function start lies outside the frozen half-open range: `0x18001ce70`. It is explicitly classified in `r16_out_of_range_callbacks.md` and appended to the master without changing the stable 362-function denominator. No additional registered function start was found at this boundary.

## Exact remaining issues

There are **no remaining P0/P1/P2 semantic blockers** for the behavior-level goal.

Two archival facts should not be mistaken for current failures:

1. `final_goal_review.md` is a pre-fix NO-GO audit timestamped before the final naming pass, r16 closure, and live-name master rebuild. Its four blockers have all been satisfied; it is superseded by this re-audit.
2. The 24 automatic live names and partial/analog/none Mac mappings are intentional confidence/scope outcomes, not missing semantic rows.

## Evidence artifacts

- `master_inventory.md` / `master_summary.json`: canonical 362-row semantic and live-name ledger.
- `naming_audit.md`: final single-snapshot live naming audit (362 frozen plus callback = 363 rows; 24 automatic, 338 named in range, zero duplicates).
- `naming_policy.md`: accepted naming policy and all 24/18 exceptions.
- `r16_out_of_range_callbacks.md`: Compute Cache callback boundary closure.
- `final_coverage_review.md`: independent address-set and target audit.

**Final semantic status: GO.**
