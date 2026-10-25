# Original-AEX UI oracle

These are original Windows AEX handler results, not Mac-plugin conformance results. `manifest.json` pins the worker, requests and raw JSONL (gzip with deterministic metadata). `build.json` pins the source and durable source archive.

Run from this OLM worktree:

```sh
python3 tests/ui_oracle/verify.py
python3 tests/ui_oracle/capture.py --worker /Users/onmk/.cache/olm-emu/worker-U03-ui/aex-guest-worker --output orchestra/state/U03-aexcompat-ui-oracle/recheck
python3 tests/ui_oracle/verify.py --replay orchestra/state/U03-aexcompat-ui-oracle/recheck
```

The first command checks committed fixture integrity and behavioral predicates only. The other commands execute all originals sequentially, then compare 17 sessions / 174 dispatches. Original binaries are read from MAIN `plugins_2025/`; they are not distributed here. `--only SESSION` selects capture sessions for investigation; full replay verification requires the complete set.

Expected replay: zero process failures and zero semantic mismatches. KiraKira serializes all 16 ramp records (325 bytes), including inactive capacity containing unstable data. Raw bytes remain intact in the witnesses. Replay compares the exact version/count/active records and every other recorded field, and separately lists sessions with raw tail differences. This does not establish raw serialization equality. An active payload or Drawbot float bit difference fails verification, as do changed requests, worker hashes, or nonzero process status.

The CLI is `aex-guest-worker ui-session ORIGINAL.aex REQUEST.json`. Each request file is a runnable example with current time and ordered operations or convenience arrays. Each output line contains setup provenance, inputs, before/after parameter and arbitrary snapshots, UI mutations, ordered recording calls and injected-state results. Exact float bits and UTF-16 data are retained. See AEXCompat `docs/olm/U03-ui-session.md` for the full protocol and fail-closed suite boundary. Pre-teardown handle counts are on stderr; successful PF setdown does not imply all plugin-acquired handles were released.

The durable cache entry is `worker-U03-ui`; it includes the worker, `build.json`, and `source.tar.gz`. `install_worker.py` documents installation and refuses to overwrite an existing worker. Never rebuild registered workers in place.

PF_Point is **x/h first, y/v second**, correcting U01's ABI note. Event click offsets are x=20/y=24; hover offsets are x=16/y=20. Frame offsets are applied according to the original conversion code.

## U04 dynamic controls

`dynamic/` extends U03 to 1,321 UPDATE dispatches across all ten plugins. It
includes every ColorKey palette row's use/replace toggles, all 32 combinations
of KiraKira Use Ramp, 363 DistanceGradation rows, and no-op Smoother/ToonDilate
controls. Requests are split at 200 operations to respect the worker's 256 limit.

```sh
python3 tests/ui_oracle/capture_dynamic.py --output orchestra/state/U04-dynamic-controls/original-recheck
python3 tests/ui_oracle/compare_mac.py --scratch orchestra/state/U04-dynamic-controls/mac-recheck --witnesses tests/ui_oracle/dynamic
python3 tests/ui_oracle/compare_mac.py --scratch orchestra/state/U04-dynamic-controls/fresh-recheck --witnesses orchestra/state/U04-dynamic-controls/original-recheck
```

The comparison compiles actual production handler bodies with real Mac SDK
headers and recording suite callbacks. It compares ordered ParamUtils and
DynamicStream mutations and all final UI flags/hidden states; parameter names
and values must not be mutated. This is a handler test, not a full EffectMain
or native AE test. Dispatch presence is checked separately in the source.
Negative controls assert dispatch absence and execute a no-op in the test host.
Every row is also checked with fresh setup UI state and its saved parameter
values. This demonstrates state reconstruction only, **not native AEP reload**.
The pinned worker cannot dispatch USER_CHANGED (13); that acceptance remains open.

Render regression helpers run sequentially:

```sh
python3 tests/ui_oracle/render_unchanged.py --base a7a82ae5411a8c9f146babc84effe4b49810d8c5 --scratch orchestra/state/U04-dynamic-controls/render-compare
python3 tests/ui_oracle/render_regression.py --phase fuzz --scratch orchestra/state/U04-dynamic-controls/fuzz-recheck
python3 tests/ui_oracle/render_regression.py --phase corpus --scratch orchestra/state/U04-dynamic-controls/corpus-recheck
```

The first compares pre-ticket/current Mac status, metadata and exact output
bytes for seed1 n300 plus every touched-plugin corpus. Source-line refusal
attribution is excluded, since inserting a UI handler shifts those line numbers.
The others execute original AEX fuzz/replay with pinned workers; an existing
mismatch/refusal is retained, and a missing historical worker fails closed.
Use a fresh scratch directory for the pre-ticket comparison; its temporary
source mirror and builds are removed on success. No original asset is copied.

`python3 tests/ui_oracle/audit_user_changed.py` audits the original decompiled
selector13 branches and pinned active vtable entries against Mac dispatch.
ColorKeep shares its UPDATE handler; the remaining nine have no UI action.
Its output is labeled `static_not_execution` and does not replace an executed
selector13 witness. The U04 corpus run recorded 914/915 saved-result matches;
RadialBlur `C46_seed1_case000280` failed inside the unchanged original worker at
RIP `0x180002860`. See `orchestra/reports/U04-dynamic-controls.md` for acceptance
limits and the retained full reports.
