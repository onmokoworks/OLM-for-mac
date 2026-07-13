# OLMBlur 16bpc residual audit

Date: 2026-07-13

## Scope

- Read:
  - `notes/IR_OLMBlur.md`
  - `notes/CONFORMANCE_LEDGER.md`
  - `refs/conformance/olmblur_*` dated `20260629..20260713`
  - `mac/OLMBlur/OLMBlur.cpp`
- Constraint: audit-only. No implementation rollback, no PNG-only tuning, no 8bpc regression work.

## Authoritative status

- Current authoritative state is `AE exact` for the declared OLMBlur 16bpc slice.
- Treat the old residual rows in the long ledger table as historical only when they conflict with newer overrides and the 2026-07-11 / 2026-07-13 evidence.

## Residual classification

### 1. pre-writeback float

- `case_0007` Legacy 16bpc is closed in this bucket.
- Windows witness at `(345,672)` records blue pre-store float `12544.498046875`, then `cvttss2si -> 12544`.
- Mac witness at the same point was `12544.5 -> 12545`.
- Classification: real Windows-vs-Mac split existed before final store; this was not a remaining writer-rule mystery.

### 2. round/writeback

- Windows PF16 writer semantics are closed: actual AEX uses add-half plus truncate, not nearest-even.
- The old Mac non-Legacy source mismatch (`nearbyintf` vs Windows add-half/truncate) was real in the historical fallback path, but the 2026-06-30 writer-only hypothesis already rejected it as a complete explanation for the sign-mixed family.
- Current `mac/OLMBlur/OLMBlur.cpp` does not drive 16bpc through that old scalar path. It dispatches 16bpc to `render_16bpc_nonlegacy_adapter` / `render_16bpc_legacy_adapter`, which call the exact worker ports.
- Classification: writer semantics are grounded, but the historical residual cannot be assigned to writeback alone.

### 3. source/kernel

- `case_0007` first had a real Legacy helper/kernel issue:
  - carry-prev state was missing in the old port;
  - then the remaining top-row family reduced to the `all_same` center-copy rule;
  - the center-copy correction made the formal 16bpc Mac AE batch exact.
- `case_0006` non-Legacy had source/kernel suspicion in late June because Mac helper dumps already diverged before `store16`.
- But the 2026-07-13 actual-AEX dependency-cone replay shows current portable worker and actual AEX are bit-exact at the tracked internal helper/pre-store/store observations for `(314,14)` and `(29,71)`.
- Classification:
  - `case_0007`: source/kernel was the real fix lane.
  - `case_0006`: no current source/kernel defect is proven by the retained evidence.

### 4. reference provenance

- This is the only bucket still open for the historical `case_0006` story.
- The older Mac single-vs-batch export split was real historically, then failed to reproduce on 2026-07-10.
- A same-run Windows current-AEX export was later imported and matched the canonical Windows Software reference at the four tracked points.
- Separately, the earlier "answered" Windows internal values for `case_0006` were retracted as unverified because no retained CDB target block backed them.
- The 2026-07-13 dependency-cone report still says the first Windows internal difference is not localized without same-run Windows typed helper/pre-store values.
- Classification: historical `case_0006` residual ownership remains reference/host-boundary/provenance-first, not an implementation-retune signal.

## Read of current implementation

- `mac/OLMBlur/OLMBlur.cpp` still contains the old scalar non-Legacy helper and `round_blur_value(... nearbyintf ...)` fallback.
- But 16bpc dispatch now goes through the exact worker adapters:
  - non-Legacy: `render_16bpc_nonlegacy_adapter`
  - Legacy: `render_16bpc_legacy_adapter`
- This is consistent with the 2026-07-11 formal Mac AE exact result and with the instruction not to reopen 16bpc from PNG-only residuals.

## Single next evidence

- One evidence item only: a same-run Windows typed internal witness for non-Legacy `case_0006`, bound to the exported PNG, at the common-core points `(314,14)` and `(29,71)`.
- Why this one:
  - it is the only retained 16bpc lane whose historical ownership is still not directly localized;
  - it can separate host/provenance drift from a genuine first Windows internal difference;
  - it does not require changing current Mac code or tuning toward PNG.

## Command

Build/validate the ready package:

```bash
python3 refs/scripts/smoke_windows_witness_olmblur_case0006_20260713.py
```

Package generator:

```bash
python3 scripts/package_windows_witness_olmblur_case0006_20260713.py
```

## FACT / INFERENCE

- FACT: the witness package smoke passes and is deterministic/fail-closed.
- FACT: the retained actual-AEX dependency-cone report is internally consistent.
- FACT: current 16bpc OLMBlur Mac AE conformance is recorded as exact for cases `0001..0007`.
- INFERENCE: if more attribution is still desired for the old `case_0006` residual, the highest-value next proof is the same-run Windows typed helper/pre-store/store witness, not a Mac implementation change.
