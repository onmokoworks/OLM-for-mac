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
