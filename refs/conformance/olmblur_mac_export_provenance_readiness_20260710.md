# OLMBlur Mac Export Provenance Readiness

- Date: `2026-07-10`
- Scope: `OLMBlur` 16bpc `case_0006` and `case_0007`; canonical/current AEX PNGs; Mac single and batch artifacts; AE runner context.
- Ownership: audit record only. No source edit, Windows package, or broad rounding change is authorized by this note.

## Decision

`case_0006` is ready for a Mac-only artifact reproducibility check, but not for a Mac-only source or pre-store conclusion. The image-level current-AEX contract is already closed by the tracked Windows current-AEX PNG: it is byte-identical to the canonical Windows Software reference. A Mac rerun can determine whether the historical single-vs-batch split is deterministic and path-specific. It cannot establish which Mac path is the Windows implementation path, nor can it decide helper/pre-store versus final-writer causality.

`case_0007` 16bpc is already closed at the relevant boundary by the Windows pre-store witness `(345,672)`: Windows `12544.498046875 -> 12544`, while Mac is `12544.5 -> 12545`. A Mac rerun is regression evidence only. The old normalized 8bpc `(488,941)` witness remains Windows-gated; the 16bpc AE runner cannot close it.

## FACT

### case_0006 identity and pixels

- Canonical and handoff-expected PNGs are identical: SHA-256 `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`, 2,485,242 bytes, 1920x1080 RGBA 16-bit.
- Tracked Windows current-AEX PNG has the same SHA-256 and byte count as canonical. Its four audited points equal canonical: `(314,14) = 2201`, `(29,71) = 725`, `(601,598) = [4609,4609,4637]`, `(378,487) = [64767,35,35]`.
- Mac single export SHA-256 is `8990ef5b4cbf82b2d86e4a6014e4d8944eff24397aa97c1fb8ceafcc310a8787`, 2,485,331 bytes. At the four points it is `[2199,727,4607,64767]` for the listed red/blue/channel-specific values in the existing audit.
- Mac batch export SHA-256 is `d99b462a4f273578c616a556cf844db515694706ae3e7fad2bc2b9c4de152974`, 2,485,333 bytes. It matches canonical at `(314,14)` and `(601,598)`, differs by `+2` at `(29,71)` and `(378,487)`, while the single export matches canonical at `(378,487)` only.
- The existing single and batch artifacts are not byte-identical and neither artifact dominates all four witness points. This is an observed artifact-path split, not evidence of a global writer rule.
- The current-AEX contract audit records parameters `Blur Amount=5`, `Blur Smoothness=100`, `Number of Repeat=10`, `Bias Direction=1`, `Legacy=0`, renderer `SOFTWARE`, bit depth `16bpc`.

### case_0007 and runner facts

- Mac single AE probe at `(345,672)` records raw blue `12544.5`, Legacy `floor(x+0.5)` stored `12545`; the corresponding Windows witness records `12544.498046875` and final word `12544`.
- The Mac single runner uses `scripts/run_ae_single_case.py`, `osascript`, and AE `DoScriptFile`; it injects request/case/output/result paths plus `OLMBLUR_DEBUG_POINTS` and `OLMBLUR_DEBUG_DUMP_PATH` through `$.setenv`.
- The historical successful single result reports AE `26.3x87`, status `ok`, and records the request directory, case id, and output PNG.
- The batch runner uses `scripts/run_ae_validation_batch.py` and `scripts/ae_pixel_validation_render.jsx`; it injects base/request/results/progress/batch-result paths and can restrict execution with `--request-id`.
- The historical 2026-06-26 batch wrapper returned `fail: 5` at the umbrella summary because all five validation groups were non-exact; OLMBlur had no missing PNG. This is expected for the residual lane and is not an AE-host startup proof.
- The older Mac automation blocker was resolved for bounded single-case runs after clearing the visible disk-cache warning and avoiding AE 26.3 `JSON.parse` on the large generated manifest. The current runner logs demonstrate request-manifest loading, parameter application, PNG creation, and `status=ok` for the successful OLMBlur probes.

## INFERENCE

- No additional Windows request is needed to establish the narrow image-level fact that the imported current-AEX export equals canonical. That fact is already proven by the current tracked PNG hash and point comparison.
- A fresh Mac single run plus a fresh Mac batch run can close a narrower local gate: whether each execution mode is repeatable, whether both use the same request and AE version, and whether the single-vs-batch divergence is reproducible. If each fresh mode reproduces its historical hash and witness pattern, classify the split as deterministic Mac export-path provenance and keep source frozen.
- If fresh single and batch converge to one identical PNG, classify the older split as stale or run-state-dependent and retain the new hash pair as the authoritative Mac artifact comparison. This still does not prove Windows/Mac pre-store equivalence.
- If either mode changes hash or witness values across repeated runs with the same request and AE host, the Mac result is nondeterministic or contaminated by host state; do not use it to justify source changes. Repeat after confirming the disk-cache/modal state and runner logs.
- A Mac PNG comparison cannot answer the remaining `case_0006` question: whether Windows and Mac differ before the final store at `(314,14)` and `(29,71)`, or whether they reach the same pre-store value and store it differently. Only typed Windows helper/pre-store evidence can answer that boundary.
- A Mac-only 16bpc rerun cannot close old normalized 8bpc `case_0007` `(488,941)`. It also must not reopen the already resolved 16bpc `(345,672)` writer question.

## Exact Mac-only execution contract

Use a fresh output root and the existing exact request. Do not modify the plugin or request manifest.

```sh
set -eu
ROOT='/Users/onmk/Documents/Projects/Personal/OLM as'
REQ="$ROOT/handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625"
OUT='/tmp/olmblur_mac_export_provenance_20260710'
rm -rf "$OUT"
mkdir -p "$OUT/single/olmblur__case_0006" "$OUT/single/olmblur__case_0007"

python3 "$ROOT/scripts/run_ae_single_case.py" \
  --request-dir "$REQ" --case-id olmblur__case_0006 \
  --output-dir "$OUT/single/olmblur__case_0006" \
  --ae-env 'OLMBLUR_DEBUG_POINTS=314,14;29,71;601,598;378,487' \
  --ae-env "OLMBLUR_DEBUG_DUMP_PATH=$OUT/single/olmblur__case_0006/blur_debug.txt"

python3 "$ROOT/scripts/run_ae_single_case.py" \
  --request-dir "$REQ" --case-id olmblur__case_0007 \
  --output-dir "$OUT/single/olmblur__case_0007" \
  --ae-env 'OLMBLUR_DEBUG_POINTS=345,672;0,0;951,7' \
  --ae-env "OLMBLUR_DEBUG_DUMP_PATH=$OUT/single/olmblur__case_0007/blur_debug.txt"

python3 "$ROOT/scripts/run_ae_validation_batch.py" \
  --base-dir "$ROOT/handoff/ae_pixel_validation_20260618" \
  --request-id ae_pixel_bitdepth16_olmblur_exact_20260625 \
  --results-base "$OUT/batch/results" \
  --progress-log "$OUT/batch/AE_PIXEL_VALIDATION_PROGRESS.log" \
  --batch-result-json "$OUT/batch/AE_PIXEL_VALIDATION_BATCH_RESULT.json"
```

The batch command may return nonzero when exact validation fails; that is not by itself a failed readiness run. Require instead: batch result JSON exists, the OLMBlur request has rendered `case_0006` and `case_0007`, no missing OLMBlur PNG exists, and the progress log reaches PNG write/result completion.

Then compare artifacts without rewriting repository files:

```sh
CANON="$ROOT/refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
SINGLE="$OUT/single/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
BATCH="$OUT/batch/results/bitdepth16_olmblur_exact/candidate/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
sha256sum "$CANON" "$SINGLE" "$BATCH"
cmp -s "$CANON" "$SINGLE"; echo "single_vs_canonical=$?"
cmp -s "$CANON" "$BATCH"; echo "batch_vs_canonical=$?"
cmp -s "$SINGLE" "$BATCH"; echo "single_vs_batch=$?"
```

Record the three fresh hashes, AE version from both result JSONs, exact request id/case ids, batch rendered/error lists, and the four `case_0006` point values. The Mac-only gate passes when both modes are `status=ok`/render-complete, metadata agrees, and repeated mode behavior is classified as either deterministic split or deterministic convergence. It does not authorize a source edit.

## Not closable by Mac-only evidence

- `case_0006` helper/pre-store versus final-writer causality at `(314,14)` and `(29,71)`.
- Any claim that the Mac single or batch artifact is the Windows current-AEX path merely because it matches selected pixels.
- Old normalized 8bpc `case_0007` `(488,941)` Windows pre-store/helper boundary.
- A global `nearbyintf` to `floor(x+0.5)` change, any helper surgery, or any broad rounding change.

## Source records

- `refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.md`
- `refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.md`
- `refs/conformance/olmblur_case0007_halfstep_family_audit_20260701.md`
- `refs/conformance/olmblur_16bpc_writer_contract_audit_20260629.md`
- `refs/conformance/olmblur_pending_final_word_proof_20260629.md`
- `refs/conformance/ae_host_automation_blocker_20260629.json`
- `scripts/run_ae_single_case.py`
- `scripts/run_ae_validation_batch.py`
- `scripts/ae_render_single_case.jsx`
- `scripts/ae_pixel_validation_render.jsx`
