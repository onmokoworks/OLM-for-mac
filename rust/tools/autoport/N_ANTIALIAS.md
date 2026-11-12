# Job N-antialias — tool changes and bounded autoport use

This job owns only `plugins/olm-anti-anti-alias` and `tools/autoport`. It does not
edit scaffold, oracle, record, witness, diverge, ubdetect, funcdb, Ghidra hub,
AEXCompat, shared crates, root Cargo manifests/lockfiles or any other plug-in.

## Changes

- `button_scaffold.py` derives the existing scaffold module and capture proxy in
  an owned directory. Exact unique anchors add PF_Param_BUTTON (15), the button
  value and `u.button_d.u.namesptr`. Source hashes are retained and changed
  anchors fail closed. This is a temporary adapter until scaffold supports
  buttons itself; it does not guess labels from the parameter name.
- `adapters.py` uses that extension. Existing capture validation stays active.
- `autoport.py` accepts a prebuilt `probe` and `target_dir`. The latter applies
  to probe/generated/final-oracle Cargo builds and artifact lookup. Paths are
  resolved at entry; the final oracle override is limited to its child process.
- `build_reference_proxy.py` packages the bridge in an isolated owned crate, records source/resource identities and verifies build-process cleanup.
- `reference_proxy.rs` is an explicit diagnostic bridge. It loads the original
  in place, observes parameter checkout/checkin, and optionally tolerates the
  first unmatched checkin after slot 2. It does not change parameter/world data
  or render arithmetic. It does **not** establish native AE semantics and must
  never be reported as the identity of an unmodified direct oracle reference.
- `record_bridge.py` derives record's controller with one reviewed change: the
  harness launches the bridge while debugger hooks target the original module.
  The underlying recorder, original hash binding, budgets and owned-job cleanup
  are unchanged. Both module identities and the source hash are retained.
- Added button/anchor/provenance and final Cargo target-scope regression tests.
  `python -m unittest discover -s rust/tools/autoport -p 'test_*.py' -v`: **23 pass**.

## Autoport outcome

The first setup attempt hit unsupported supervised button declarations. The
scoped extension resolved it. An initial empty-corpus configuration was refused
before a Codex call; no function was verified from an empty vector set.

`runs/n-antialias-leaves-v2` admitted two reviewed pointer contracts and ordered
these leaves. RVA 0x1680 (16-bit color membership) and 0x1740 (8-bit membership)
each needed two generations to preserve unordered floating comparisons. Each
passed 512 native vectors. Four Codex calls; total recorded attempt time
64.313 seconds (31.188 + 33.125). The controller correctly stopped at
`needs_human`; this is not full render-graph coverage.

The existing bounded `budget_codegen.py` then generated RVA 0xa630 from a
manually recovered 10-argument ABI, decompilation and assembly. Three Codex
calls corrected duplicate-color NaN handling and the exact addition grouping
of the score. Generation elapsed time was 112.781 seconds in the ledger.
The final production helper passed 1,024 native vectors and eight real-render
recorded-call replays, including all output-buffer bytes and return bits.

**Total: seven Codex calls (limit 80), three generated production functions.**
Ghidra contracts, object layouts, plateau detection, three image passes,
parameter snapshots and AEGP UI/storage wiring were manual work. No full-plugin
autogeneration or per-function verification of every manually translated image
pass is claimed. See the plug-in VALIDATION.md for integration coverage.

## Requests for the owning tools

1. Scaffold: implement supervised PF_Param_BUTTON capture/emission natively.
2. AEXCompat: preserve a dedicated duplicate-checkin reproduction and decide
   its compatibility contract using native AE evidence. The reference returns
   error 4 after checkout(1)/checkin, checkout(2)/checkin, then a second checkin
   of that same parameter address. Do not globally relax checkout ledgers on
   the strength of this diagnostic bridge alone.
3. Oracle: identify external modules loaded by a forwarding reference and bind
   required environment controls in the case manifest. These runs supplement
   that missing identity in a separate provenance file.
4. AEXCompat: investigate session-open `os error 80` collisions observed in two
   final Smart16 reference processes; retain baseline failures and exact replay
   outcomes rather than rewriting the original campaign result.

No original binary was copied or modified. Raw run directories remain local.
The job used an isolated Ghidra project/port; its lifecycle is recorded in the
plug-in's validation evidence.
