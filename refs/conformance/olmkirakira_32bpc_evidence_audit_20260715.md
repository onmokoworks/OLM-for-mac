# OLMKiraKira Imported Windows 32bpc Evidence Audit

Date: 2026-07-15

## Decision

Smallest candidate: `final_random10_olm_kira_kira_06` (one fully pinned case). It uses Blur Mode 2, Merge mode 1, and `Approximated Input=0`; it does not depend on unresolved Mode3 Gaussian behavior.

Status: **candidate identified; Mac validation pending**. This is not an AE exact claim.

## Imported EXR audit

- Windows manifest: `refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMKiraKira/reference_manifest.json`.
- Cases: `10`; all cases have 42 parameter records and complete property identity/value metadata.
- Every before-effects/effect-on file inspected has 1920x1080, A/B/G/R channels, FLOAT sample type `2`, and uncompressed scanline compression `0`.

| Family | Cases | Eligibility |
| --- | --- | --- |
| Blur Mode 1 | `02, 05, 08` | grounded dispatch candidate |
| Blur Mode 2 | `06, 09` | grounded three-box candidate |
| Blur Mode 3 | `03, 07, 10` | excluded; Gaussian unresolved |
| Blur Mode 4 | `01, 04` | excluded; behavior unresolved |
| Strength zero | none in imported 32bpc set | no 32bpc strength-zero candidate present |

## Selected pin

- Case: `final_random10_olm_kira_kira_06`.
- Input: `random_final_alpha_1920x1080`.
- Parameter SHA-256: `cf30acd083b7a8836b54a7a7a0d3bee51ce4d181c94ee5b22d1cb82fdd982d5b`.
- Before-effects EXR SHA-256: `27e55775eb4b6b038ac04f10b56e5800904efb658864ff4c1c64ed0728ae2676`.
- Effect-on EXR SHA-256: `5dc720b60b1e453c75787f0948560fa712fb66399a2390f583ab448f17288830`.

## Mac contract

Request: `refs/mac_validation_requests/olmkirakira_mode2_32bpc_mac_validation_20260715.json`.
It requires the exact 42-property pin, the Windows input/output hashes, loaded plugin SHA-256, same-comp before-effects control, uncompressed FLOAT RGBA EXRs, Output Module settings capture, and raw FLOAT32 equality before any exactness status can be emitted.

## Limits

No retuning was performed. No production source, Mode3 live-Gaussian/aggregation lane, shared ledger/orchestration, or generic reference checker was changed. PNG, CLI, emulation, visual similarity, and unresolved Mode3 evidence cannot satisfy this contract.
