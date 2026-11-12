# Turn 2: full render qualification

Both requested plug-ins pass the unchanged public `olm_oracle.py check --full`
workflow. Evidence is retained in `runs/turn2/qualification.json`, with complete
oracle reports in `toon-full/oracle/summary.json` and `color-full/oracle/summary.json`.
The new crates are `runs/turn2/toon-work` and `runs/turn2/color-work`.
These are generated work crates, not modifications to the production plug-ins.

| Plug-in | Smart8 | Smart16 | Smart32 | Inventory | Oracle elapsed |
|---|---:|---:|---:|---|---:|
| OLMToonDilate | 20/20 exact | 20/20 exact | 20/20 exact | identical | 48.406 s |
| ColorKeep | 20/20 exact | 20/20 exact | 20/20 exact | identical | 47.860 s |

Classic routes are correctly not applicable under these originals' declared
SmartFX dispatch contracts. There were no integrated mismatches, so `diverge`
was not invoked. This is the tool's full 20-case corpus per depth, not exhaustive
verification of all parameter combinations, error paths, ROI, concurrency, or AE.
The run used headless AEXCompat only. No GUI, AE, commits, or pushes were used.

## Cost and generated functions

| Generation unit | Attempts | Codex elapsed | Whole attempt elapsed | Result |
|---|---:|---:|---:|---|
| Toon depth-parameterized worker (three original workers) | 1 | 62.594 s | 80.038 s | recorded native witness exact |
| Toon parameter snapshot and scaffold adapter | 1 | 61.781 s | 146.250 s | full oracle PASS |
| Color parameter snapshot, root loop, scaffold adapter | 1 | 103.328 s | 133.529 s | full oracle PASS |

**3/60 Codex calls**, 227.703 s generation, 359.817 s total attempt time.
The cap was four attempts per generation unit and 300 s per attempt. Each Codex
child had a 240 s hard timeout, leaving validation time. Oracle qualification
was separately bounded at 240 s per plug-in and two render workers. Model was
the CLI default with medium reasoning; `--model` and `--effort` are configurable.
This run did not pin a model version. All three attempts completed under 300 s.

Nine Turn 1 generated leaf functions were reused (six Toon and three Color).
Turn 2 generated three depth-specific Toon worker behaviors as one Rust function,
and both adapters, including Color's snapshot and render loop. No generated unit
exhausted its retries or remains `needs_human` for the declared full-oracle routes.
This does **not** mean every node of the original C++ runtime graph was translated:
host suites remain host calls; OpenCV temporary storage was lowered to Rust-owned
storage. Historical Turn 1 graph state remains unchanged as evidence of that run.

## Closing blockers 1–3

1. **Recorded ABI and host state.** `capture_context.py` extends the public
   recorder with bounded pointer follows. Twelve Toon renders cover all depths,
   7x5/radius2, 3x7/radius0, 11x7/radius3.25/downsample1/2, and 1x1/radius100.
   PF_InData, world headers, pixel buffers, radius and suite tables are retained.
   `native_context.rs` supplies recovered host allocation/copy services, loads the
   original in a witness child, and calls its real worker RVA. Every captured
   after-buffer matches on all twelve calls. The generated worker matches those
   twelve calls as well. World data-pointer identities are relocated; their full
   backing buffers are compared separately, not ignored.

   `capture_color.py` records the parameter parent and first two pixel callbacks
   per depth, plus all 101 checkout replies and all 100 floating-color replies.
   `native_color.rs` replays those actual host inputs into the original parameter
   parent. `replay_color.py` reproduces all three 1,640-byte contexts exactly,
   apart from the two documented relocated pointer fields. It does not implement
   or substitute the original algorithm. The generated adapter calls the real
   host color suite; it does not embed captured palette answers.

2. **Indirect calls and library dependencies.** `toon-callback-trace-v2` records
   actual copy, acquire, new-handle and lock-handle calls and provider RVAs.
   Color records checkout/acquire/color-conversion calls. `root-xrefs.json`
   retains hub xrefs; `hub-annotations.json` records six comment-only mappings.
   Imported human names were preserved. The selected hub was started by this job
   as PID 59280; ownership identity is retained in `hub-owned.json`. After a
   final status and identity check it was stopped gracefully: `hub-stop/stdout.txt`
   confirms exit, no forced termination and no remaining owned PIDs.

   Completed funcdb `lookup` results are retained for both originals. Its only
   three already-covered mappings in each target refer to the prohibited target
   implementations. They were excluded; no verified target Rust or C++ bodies
   were opened or supplied to Codex. There was no independently qualified shared
   Rust callee to import on these selected paths. Unverified library-name matches
   were not promoted to known functions. The nine own generated leaves remain
   admissible by their original witness evidence.

3. **Render adapter.** Source-blind Codex calls received decompiled C with hub
   comments stripped, own generated callee signatures, scaffold AE code and the
   recovered contracts. Tool access was disabled and JSONL checked for tool use.
   Toon checks out the radius and calls its generated worker. Color snapshots the
   integer count and all 100 colors using the host float-color suite, then calls
   the generated root around the three qualified pixel callbacks. The scaffold's
   metadata, parameter setup, SmartFX acquisition and cleanup layer stays in place.
   The full oracle builds and tests those independent crates. There is no runtime
   original-DLL delegation in either candidate.

## Reproduce and resume

All prompts, answers, token usage, command logs, captured snapshots, witness
results, binaries and oracle cases remain under `runs/turn2`. Generation reserves
its durable budget before starting; interrupted calls are never refunded.
Rerunning the report is read-only except for rebuilding `qualification.json`:

```powershell
python rust/tools/autoport/turn2_report.py rust/tools/autoport/runs/turn2
python -m unittest discover -s rust/tools/autoport -v
python rust/tools/autoport/full_check.py rust/tools/autoport/runs/turn2/toon-work --original ../ghidra_windows_aex/OLMToonDilate.aex --name autoport-toondilate --out rust/tools/autoport/runs/toon-recheck
python rust/tools/autoport/full_check.py rust/tools/autoport/runs/turn2/color-work --original ../ghidra_windows_aex/ColorKeep.aex --name autoport-colorkeep --out rust/tools/autoport/runs/color-recheck
```

Use fresh output directories for execution; retained evidence is not overwritten.
All 20 Python unit tests passed, including the turn-wide budget boundary checks.
`full_check.py` only redirects the workflow's artifact/target root into autoport;
it does not change comparisons or dispatch rules. Native replay examples:

```powershell
python rust/tools/autoport/replay_context.py rust/tools/autoport/runs/turn2/capture8 --module rust/tools/autoport/runs/turn2/native_context.dll --original --out rust/tools/autoport/runs/toon-native-recheck
python rust/tools/autoport/replay_color.py rust/tools/autoport/runs/turn2/color-record8 --module rust/tools/autoport/runs/turn2/native_color.dll --out rust/tools/autoport/runs/color-native-recheck
```

## Remaining manual steps for a new plug-in

These demonstrations close the three blockers for the tested routes, but the
new context recovery is **assisted, not a general automatic ABI inference engine**.
A new plug-in still needs a reviewed recording profile (RVA, register/stack ABI,
pointer follows and bounds), host-service replay definitions, and identification
of persistent state versus invocation inputs. Here those profiles and the two
native host bridges were written manually; Codex generated the image algorithm
and integration code. The generic Turn 1 graph runner does not yet synthesize or
schedule these new profiles itself. The Turn 2 scripts and budget ledger form a
reproducible staged workflow rather than a one-command arbitrary-plugin port.

Next work: express context follows and service reply routing declaratively;
derive candidate offsets from multiple varied recordings; automatically qualify
the recovered parent before graph admission; register reusable host-contract
adapters and qualified shared functions; connect integrated mismatch output to
`diverge`; and add held-out seeds, nondefault palettes, ROI and injected failures.
Color's recorded-parent corpus uses two enabled default colors, while the full
oracle adds its standard parameter variations. It is not a proof for arbitrary
host color transforms. Successful full renders also do not prove allocator-error,
exception, asynchronous callback or vtable lifetime equivalence.

One optional first Toon callback trace failed because record's loaded-module list
excluded the process image. The autoport extension now resolves that image's
allocation base for observed targets; the second trace succeeded. Both attempts
verified cleanup. No other tool's sources were changed.
