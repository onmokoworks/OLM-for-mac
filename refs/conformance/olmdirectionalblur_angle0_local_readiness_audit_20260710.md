# OLMDirectionalBlur Angle-0 Local Readiness Audit

- Date: `2026-07-10`
- Scope: local readiness only; no source, package staging, or PNG changes
- Decision: `contract-self-consistent-but-not-locally-executable; typed-witness-still-missing`

## FACT

- The prepared contract is
  `refs/conformance/olmdirectionalblur_angle0_single_shot_witness_contract_20260708.md`.
  It names request `olmdirectionalblur_angle0_single_shot_witness_20260708`, case
  `db_existing_case_0001_software_pair`, source request set
  `directionalblur_context_scale_20260606`, lane `angle0-rowdriver-valid-alpha`,
  and exactly two same-run pixels: `(494,169)` and `(579,169)`.
- The packaging code exposes the matching profile
  `directionalblur-angle0-single-shot-witness`, selects the same contract as its
  entrypoint, and pins execution to that one request. Its stop condition and
  required fields agree with the contract.
- The source request JSON contains the named case with `Angle=0`, front strength
  `1690`, front alpha fade `0`, sharp tail `45`, size variation `92`, and common
  front-only settings. The required render set is Software.
- The request/profile is therefore internally self-consistent. It is executable
  in principle by the Windows external-trace workflow, but no prepared
  single-shot zip is present locally in `refs/runtime_trace_packages` or
  `refs/share_staging`; only the generator/profile definition and contract are
  present. This audit does not stage or generate it.
- `refs/reports/runtime_trace_summary.json` has no DirectionalBlur result. The
  latest listed result is a DistanceGradation partial return, so there is no
  single-shot live return to compare.
- The prior helper-gate return is explicitly `answered_partial`: it proved module
  and broad stage reachability but did not retain typed values for either target
  pixel because broad helper auto-continue caused a hit storm.
- The comparator smoke passes:

  ```text
  python3 refs/scripts/smoke_compare_directionalblur_trace.py
  [OK] DirectionalBlur trace comparison smoke
  ```

  This verifies comparator behavior only; it is not a Windows trace result.
- Current static AEX/IR facts retain the following boundary: the front helper
  uses an effective span `int(strength * coeff)`, offsets `1 <= offset < span`,
  writes strictly left of its source x, reads source RGB from A, reads its
  alpha/validity input separately, accumulates a separate denominator, and the
  final RGB normalization is guarded by `denom > 0`.
- The local angle-0 row segment is `x=380..579` on `y=169`. Thus the endpoint
  `(579,169)` cannot be explained by a same-row front-helper source inside that
  visible segment alone; a useful trace must expose a source x beyond the
  endpoint, a rotated-buffer/group mapping, or an alternate validity path.
- Current Mac static code has a useful but limited fact: it reads
  `downsample_x` and `downsample_y` from `PF_InData`, and at angle zero its
  directional scale reduces to `scale_x`; front strength is then truncated
  after that scale. The Mac 8bpc implementation otherwise performs a direct
  same-row bilinear gather, keeps `accum_sum` and max-like alpha, and divides RGB
  by fixed scaled front strength. It copy-throughs nonzero alpha-fade/noise/back
  lanes and all 16/32bpc paths.

## INFERENCE

- The request is ready for a Windows trace operator once the package is actually
  materialized and transferred. It is not locally runnable as a complete
  external-trace request because the package/Windows debugger session is absent.
- The exact missing typed witness is two independent records, one for each of
  `(494,169)` and `(579,169)`, from the same Software render and same execution:

  1. normalized parameters actually consumed;
  2. output-to-A/B coordinates plus buffer identity, or explicit rotated-buffer
     mapping;
  3. helper-local source x/y and source-x range, or an explicit alternate-path
     explanation for `(579,169)`;
  4. touched destination x range on row `169`;
  5. rowdriver/group membership;
  6. denominator;
  7. `alpha_or_valid` or equivalent validity side-channel;
  8. accumulation numerator RGBA;
  9. pre-writeback RGBA float/hex;
  10. final stored RGBA bytes.

- Final PNG bytes, broad breakpoint counts, module-load/stage reachability, or a
  single case-level value set are insufficient and remain `failed_partial` or
  `failed` under the contract.
- The Mac-only scale fact can narrow context-scale interpretation: for this
  angle-0 case, a valid Mac `downsample_x` observation would affect the consumed
  strength while `downsample_y` should not. It cannot identify the missing AEX
  rowdriver/group or hidden validity behavior, because the current Mac path is a
  direct gather rather than the traced A/B/helper choreography.
- No Mac source change is justified by this audit. The existing Mac Gaussian
  divisor parity (`length/3.0`) is already recorded as a narrow static patch and
  does not answer the angle-0 witness.

## Commands

```bash
python3 -m json.tool refs/reference_requests/directionalblur_context_scale_20260606.json
python3 refs/scripts/smoke_compare_directionalblur_trace.py
python3 scripts/package_runtime_trace_requests.py --help
find refs/runtime_trace_packages refs/share_staging -type f | rg 'directionalblur_angle0_single_shot|directionalblur.*single_shot'
python3 - <<'PY'
import json
d=json.load(open('refs/reports/runtime_trace_summary.json'))
print([(r.get('request_id'), r.get('status')) for r in d.get('results', [])])
PY
nl -ba mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp | sed -n '191,199p;226,325p;365,386p'
nl -ba cli/OLMDirectionalBlur/main.cpp | sed -n '525,535p;1216,1225p;1275,1323p'
```

## Readiness

- Prepared request/profile: `self-consistent`.
- Locally executable now: `no`; no single-shot package or live Windows return is
  present.
- Required next artifact: one Windows return containing the two complete typed
  per-pixel records above, captured with conditional/single-shot gating and no
  diagonal witnesses.
- Until that return exists, keep both Mac and CLI implementation behavior
  unchanged for this lane.
