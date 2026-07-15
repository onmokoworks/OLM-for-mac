# OLMBlur case_0006 Mac observation request 2026-07-15

Status: `sendable_fail_closed`; observation lane only.

The request performs exactly one existing-After-Effects run of the current
Mac OLMBlur case `olmblur__case_0006` at 1920x1080, 16bpc, Software, with the
retained parameters `5 / 100 / 10 / 1 / Legacy=0`. The env-gated contract
records the final 16-bit store observation at the residual locus `(601,598)`
and the same run writes the case output PNG and diagnostic log to one fresh
output directory.

Before touching AE, the runner resolves the installed Mac `OLMBlur.plugin`
binary and computes its SHA-256. The run is allowed only when it equals the
pinned instrumented Debug binary
`c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206`.
The diagnostic record carries this Mac plugin hash; the Windows AEX hash is
not accepted as evidence of which Mac binary AE loaded.

The tracked request contract lives at
`refs/mac_validation_requests/olmblur_case0006_mac_observation_20260715.json`.
It is intentionally outside `refs/reference_requests/`, which is reserved for
pending Windows reference requests.

The runner refuses reused output directories, wrong AE result metadata, stale
or non-RGBA16 output, missing logs, missing fields, identity drift, or any
diagnostic record count other than one. It emits `answered_observation` with
`claim=observation_only_not_exact`; it does not compare or claim exactness.

Run only from a Mac with After Effects already open:

```sh
python3 scripts/run_olmblur_case0006_mac_observation_20260715.py \
  --output-dir /tmp/olmblur_case0006_observation_20260715
```

No AE installation, launch, algorithm retuning, shared ledger update, or
source change is part of this request.

Verification without AE:

```sh
python3 tools/emulation/test_olmblur_case0006_mac_observation_20260715.py
```
