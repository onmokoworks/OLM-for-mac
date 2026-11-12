# Function-by-function automatic porting

**Turn 2 update:** both OLMToonDilate and ColorKeep now pass `check --full`:
20/20 exact cases on each declared Smart8/16/32 route. Three additional Codex
calls generated the worker and adapters using recovered recorded contracts.
See [TURN2.md](TURN2.md) for evidence, timings, reproduction and remaining manual
ABI-recovery work. The historical Turn 1 results below are retained unchanged.

## Turn 1 baseline

This is a working, bounded translation/witness loop, **not an unattended complete
AE plug-in porter**. On the real ColorKeep and OLMToonDilate originals it generated
and verified nine Rust functions, automatically repaired one float mismatch, and
then stopped at unresolved parent/host contracts. Both final render oracles
correctly reported **FAIL** for the incomplete scaffold. No full render port,
native AE acceptance, or macOS qualification is claimed.

All implementation files are in this directory. Existing scaffold, witness,
oracle and Ghidra hub sources are imported/called without editing them. The tiny
Cargo package satisfies the parent's `tools/*` workspace glob; Python implements
the orchestrator. Generated code using `olm-math` is OLM-internal and must not be
published standalone.

## Run and resume

Requirements: Windows x64, Python 3.11 with `pefile`, Pillow/NumPy for the kit,
Rust/MSVC and cached offline Cargo dependencies, the installed native Codex CLI
and its existing authentication, built `witness/target/release/witness-host.exe`,
and the shared AEXCompat harness. No AE, GUI, installation, Git operation,
watcher, or unrelated MCP is used.

Use the persistent hub described in [`../ghidra-hub/README.md`](../ghidra-hub/README.md).
Run `status` first; share an existing instance. If you start one, retain its
returned PID/token and stop only that instance after all its users finish.
The orchestrator connects through the Python HTTP client; it never opens a
Ghidra project or launches throw-away headless analysis.

```powershell
& D:/olm-rs-ghidra/venv/Scripts/python.exe rust/tools/ghidra-hub/hub.py status
# Only when stopped:
& D:/olm-rs-ghidra/venv/Scripts/python.exe rust/tools/ghidra-hub/hub.py start

python rust/tools/autoport/make_demo.py
python rust/tools/autoport/autoport.py rust/tools/autoport/local/configs/ColorKeep.json --out rust/tools/autoport/runs/my-colorkeep
python rust/tools/autoport/autoport.py rust/tools/autoport/local/configs/OLMToonDilate.json --out rust/tools/autoport/runs/my-toondilate
```

Repeat the **same command and output directory** to resume. Completed functions
are not regenerated. Config, original identity, graph identity (new checkpoints),
and verified source hashes must agree. Interrupted attempts consume their reserved
time and an attempt slot. Exhaustion is `needs_human`; a fresh output directory
is required for changed inputs/budgets. An OS file lock excludes simultaneous
controllers. Setup uses retained staging directories; an interrupted final oracle
gets a new numbered output directory. The initial two evaluation runs predate
atomic scaffold staging; their complete work crates remain usable.

Exit 0 requires a covered, integrated render path and a passing oracle. Exit 2
means incomplete/needs-human work; Ctrl+C returns 130 after cleanup. Unexpected
configuration/setup exceptions remain errors with their traceback and logs.

`--model MODEL`, `--effort low|medium|high|xhigh`, and `--codex PATH` are configurable.
The default uses the installed CLI's model; pin a model for comparable campaigns.
The generator receives a UTF-8 **prompt file via stdin** (`codex exec ... -`) and
returns schema-constrained JSON. The controller writes its `code` into
`work/src/autoport/f_<address>.rs`. `--ignore-user-config`, ephemeral sessions,
read-only mode, disabled shell/apps/multi-agent/web, no project instructions,
and an explicit no-tool prompt isolate this narrow generator. Logged tool calls
invalidate the attempt. This is an evaluation boundary, not a hardened hostile-code
sandbox. Global CLI skill descriptions may still add context/token overhead.

## Pipeline and evidence gates

1. Verify the AEX SHA-256 against the hub program. Walk direct calls from supplied
   render roots, retain the frontier when the node budget ends, batch-decompile
   sequentially through the hub, and preserve signatures, full original C and
   normal/delay imports. No whole-binary re-analysis runs. Graph cycles and their
   ancestors remain blocked; unresolved imports require verified wrappers.
2. Generate a real scaffold using its public resource, inspection, declaration
   capture and `emit` functions. Build the capture proxy into this run, stage a
   normal single-link copy for AEXCompat, and add `olm-math` plus generated modules.
3. Schedule leaves before callers. A caller sees the already verified callee
   signatures. A reviewed `contracts` entry defines each pointer ABI and corpus.
   `infer_scalars: true` optionally admits conservatively parsed scalar-only C;
   unknown types, pointers and recovered global-state artifacts are refused.
   Scalar inference is a heuristic and was not used in the measured demos.
4. Strip imported comments from generator C to avoid leaking translated source
   excerpts. Keep the original annotated export for the auditor. Prompts require
   UCRT `olm_math` calls, explicit FMA/NOFMA lane, no std transcendental calls,
   exact types/order, and x86 conversion semantics. Current prompts include only
   imports referenced by that function; the original measured prompts included
   all module imports, so the measured token totals are not estimates of the
   reduced-context version.
5. Compile the generated Rust into the scaffold DLL. Find its export RVA from
   the PE export table, then use **witness on both the original and Rust DLL**.
   Compare declared return bits and complete buffers, including inputs, padding
   and guard gaps. Do not compare undefined RAX for void returns. Each vector has
   independent allocated state; aliasing within a vector is preserved. Relocated
   pointer fields use an arena self-pointer to normalize ASLR addresses, rather
   than ignoring their offsets. FMA lane, nearest rounding and gradual underflow
   are checked. The native witness also records UCRT/module identities and guards.
6. A mismatch is reduced to one failing call and rerun independently. Only a
   reproduced case is fed back with expected/actual bytes. This is **case-level
   minimization**, not a claim of minimal numeric values or buffer dimensions.
   Stateful failures that cannot reproduce as one call require a sequence ABI.
   Compile/setup/native failures remain distinct from numerical mismatch evidence.
7. Atomically save state and a Markdown progress table after each attempt. Append
   verified mappings through hub `bulk_edit`, merging the current comment and
   preserving the name with `expected_name`; never rename imported human symbols.
8. All internal graph functions must be verified, the frontier empty, and indirect
   coverage explicitly reviewed before integration is eligible. A supplied,
   hash-bound `integration.files` adapter is copied only into `work/src`. Automatic
   AE suite/parameter/ROI adapter synthesis is **not implemented**. Regardless of
   incomplete coverage, the demo runs the public `olm_oracle.py check` workflow
   to expose the scaffold's real render result, labeled `incomplete scaffold`.

`check` currently hardcodes its Cargo target under its own tool directory. A
small child driver redirects that module's `HERE` constant to this run before
calling the unchanged public CLI implementation. This keeps its generated Cargo
target and all oracle artifacts in autoport. An upstream `--target-dir` option
would remove that adapter. Similarly, a scaffold `--capture-out` option would
allow using its CLI directly instead of composing its public functions.

Generated artifacts live in ignored `runs/` and `local/`. Each run retains:

```text
config.json, graph.json, exports/<address>.c
state.json, progress.md, annotations.json
setup/, probe-target/, capture.aex, work/
functions/<address>/vectors.json, contract.json
functions/<address>/attempt-NN/prompt.txt, schema.json, answer.json, function.rs
functions/<address>/attempt-NN/codex/{stdout,stderr}.txt, process.json
functions/<address>/attempt-NN/build/, original/, rust/, comparison.json
functions/<address>/attempt-NN/minimal-{original,rust}/  # on mismatch
oracle/summary.json, oracle/render/, oracle-process/, oracle-owned/
```

The two initial evaluations did not emit `contract.json`; their exact contracts
are in `config.json`. All submitted witness specs, vectors and answers are retained.

## Configuring another function

Use `make_demo.py` as executable examples of pointer ABI contracts. Configuration
must supply `program`, absolute `aex`, `crate_name`, `roots`, and `contracts`.
`root_evidence` explains manually resolved indirect render roots. The demo chooses
ColorKeep's dispatcher plus its three pixel callbacks, and ToonDilate's
`MyEffect` SmartRender vtable target grounded by the imported hub annotation.
Root selection and pointer layouts are reviewed inputs, not automatic discoveries.

Each contract has `abi: {args: [...], return: ...}`, an exact `rust_signature`,
`notes`, and a `fixture`: `scalar`, `recorded`, `color8/16/32`, `copy8/16/32`, or
`unpack8/16/32`. Native types follow witness (`ptr`, integer widths, `f32/f64`,
return-only `void`). Raw pointer returns are not a portable equality contract;
use a reviewed output-buffer wrapper instead.

`recorded` appends inline vector objects to generated inputs. `recorded_files`
accepts `[{"path":"absolute vectors.json", "sha256":"..."}]`. Each file is a
list of `{label, buffers, args, return}` objects using witness buffer/argument
syntax, with inline hex rather than file references. Outputs are never supplied
as expected-value tables: both native functions compute them. Zero-length corpora
cannot pass. The standalone replay command uses actual retained original inputs:

```powershell
python rust/tools/autoport/replay_verified.py rust/tools/autoport/runs/my-colorkeep --out rust/tools/autoport/runs/my-recorded-replay
python rust/tools/autoport/report.py rust/tools/autoport/runs/my-colorkeep --out rust/tools/autoport/runs/my-colorkeep/report.json
```

Optional `known_functions` names a verified funcdb exchange JSON with a
`functions` array. Each entry needs `verified:true`, `original_sha256`, `address`,
`rust_signature`, `rust_source`, `rust_sha256`, `evidence`, `evidence_sha256`.
Paths resolve relative to the exchange; hashes are mandatory. Source must export
the expected `autoport_<address>` symbol. Name/shape-only matches are never
accepted. `rust/tools/funcdb` was absent during this evaluation, so this optional
exchange was skipped. A live funcdb-native lookup adapter awaits its published API;
the exchange is a documented autoport contract, not an invented funcdb API.

`integration` has the form
`{"files":{"src/algorithm.rs":{"path":"...","sha256":"..."}}}` and may
include a reviewed `src/ae.rs` adapter. All destination paths must stay under
the generated crate's `src`. Set `indirect_reviewed:true` only with actual
coverage evidence. Neither the config flag nor a scalar witness establishes
unseen render branches.

## Measured run: 2026-11-12

Original SHA-256s:

- ColorKeep: `6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86`
- OLMToonDilate: `c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3`

No existing verified Rust plug-in or C++ implementation was given to the
generator, nor were those sources used to author its functions. The controller
supplied decompiled C, ABI/layout contracts and numeric rules. `olm-math` is the
explicit permitted numeric library. The ten generator JSONL logs contain **zero
shell, file-change, web or MCP tool events**.

Budget per plug-in: at most **8 admitted functions × 2 attempts**, **90 seconds
generation per attempt**, **120 seconds total per attempt**, **240 seconds per
function**. Setup commands: 300 seconds each; native witness child: at most 20
seconds, also limited by the remaining attempt deadline; final oracle: 600
seconds, jobs 2. Process termination has a bounded cleanup grace in addition to
the work deadline. Ghidra export is capped, with 30 seconds per decompilation.
The first Toon export admitted six cheap external placeholders beyond the
nominal 120-node bound; subsequent exports enforce the cap on placeholders too.

Actual generation: **10 Codex calls**, CLI default model (not pinned), effort
`low`. Reported usage: **183,459 input tokens** (12,288 cached), **5,447 output
tokens**; the CLI also reported 868 reasoning-output tokens. No dollar cost is
inferred from an unpinned model. Total function-attempt wall time was **175.233s**;
setup/export/oracle time is separate. No attempt hit its timeout.

| Original / function VA | Role | Attempts | Total seconds | Exact vectors |
|---|---|---:|---:|---:|
| ColorKeep `180001280` | PF16 pixel callback | 1 | 27.906 | 198 |
| ColorKeep `180001580` | PF8 pixel callback | 1 | 26.531 | 198 |
| ColorKeep `180001850` | PF32 pixel callback | 2 | 55.125 | 198 |
| ToonDilate `1801ac6c0` | PF8 unpack to float | 1 | 8.875 | 64 |
| ToonDilate `1801ac730` | PF16 unpack to float | 1 | 14.093 | 64 |
| ToonDilate `1801ac7a0` | PF32 unpack | 1 | 11.625 | 64 |
| ToonDilate `1801ac880` | PF8 ordered pixel copy | 1 | 9.344 | 64 |
| ToonDilate `1801ac8b0` | PF16 ordered pixel copy | 1 | 10.547 | 64 |
| ToonDilate `1801ac8e0` | PF32 ordered pixel copy | 1 | 11.187 | 64 |

ColorKeep corpus: counts -1, 0, 1, 2, 3, 4, 5, 7, 8, 9 and 24; matching and
nonmatching palettes; float raw words including signed zero, subnormals, extrema,
quiet/signaling NaNs and infinities. Integer-depth palettes also include those
float edges. Toon corpus: 64 vectors per helper with integer edges and random
words; PF32 raw float edges; copy helpers include null, identical and overlapping
pointers with distinct initial bytes. Seed: **20261112**. This samples the stated
domains; it is not exhaustive function equivalence.

**Real feedback correction:** ColorKeep PF32 attempt 1 failed vector 45,
`pf32-count1-v9`. Its unordered float comparison cleared alpha where the original
kept it. The one-call replay reproduced the mismatch. After receiving that vector
and byte difference, Codex changed the comparison from ordered `<=` to
`!(magnitude > threshold)`. Attempt 2 passed all 198 vectors. There was no human
edit of either generated function and no expected-result substitution.

Graph coverage: ColorKeep **3/18 internal nodes** verified, plus 7 external
nodes blocked; no static frontier remained. ToonDilate **6/95 internal nodes**
verified, plus 31 external placeholders; **3 frontier targets remained** at the
export budget. These are the selected render-root graphs, not percentages of all
machine-code functions. Indirect calls remain unresolved in both.

The final `olm_oracle.py check` ran through the public workflow for both generated
crates. Inventory was identical in both. Per-depth counts below use six cases at
Smart8/16/32, downsample cycling 1, 1/2, 1/4 and the oracle's default size cycle
1×1, 3×7, 97×61, 256×144. Classic routes were not applicable.

| Incomplete scaffold | Smart8 exact / mismatch | Smart16 | Smart32 | Final oracle |
|---|---:|---:|---:|---|
| ColorKeep | 2 / 4 | 2 / 4 | 2 / 4 | **FAIL**, exit 1 |
| OLMToonDilate | 3 / 3 | 3 / 3 | 3 / 3 | **FAIL**, exit 1 |

No reference failures, candidate failures or timeouts occurred. Passing identity/
no-effect cases do not establish integration. The verified helpers are compiled
in the crate but **not connected to its still-copying render adapter**.

Retained local evidence:

- [ColorKeep progress](runs/colorkeep-v1/progress.md), [report](runs/colorkeep-v1/report.json), [oracle](runs/colorkeep-v1/oracle/summary.json)
- [ToonDilate progress](runs/toondilate-v1/progress.md), [report](runs/toondilate-v1/report.json), [oracle](runs/toondilate-v1/oracle/summary.json)
- [PF32 failing vector](runs/colorkeep-v1/functions/180001850/attempt-01/comparison.json)
- [ColorKeep recorded replay](runs/colorkeep-recorded-replay-final/summary.json), [Toon recorded replay](runs/toondilate-recorded-replay-final/summary.json)
- [Owned timeout cleanup](runs/process-timeout/result.json)

All **978 retained inputs** were replayed against both originals and the final
generated DLLs, again exact. Both saved controllers resumed without another
generator call. The shared hub was started by another job between this job's
initial stopped status and start request; `start` returned existing PID **3632**.
It was shared and left running. Nine comment mappings were persisted without
renaming functions. The controlled timeout test terminated exact child PID 5136
and descendant 51804 in 1.532 seconds; both were confirmed absent. Every outer
autoport command/native witness job reported verified cleanup, including the
oracle process tree. The oracle's individual inner records do not expose a
cleanup boolean; their enclosing owned job provides the process-tree check.

Initial setup incident: passing a Cargo hardlinked capture DLL to AEXCompat was
rejected before any generator call. The unchanged scaffold CLI created diagnostic
directory `rust/tools/scaffold/local/capture-11ipphif` for that failed attempt.
It was left intact; no other job's artifacts were removed. The adapter now stages
a normal Rust-proxy copy and roots capture evidence under autoport. The originals
were never copied or modified.

## Verification and next improvements

```powershell
python -m unittest discover -s rust/tools/autoport -v
python rust/tools/autoport/validate_process.py --out rust/tools/autoport/runs/new-timeout-test
```

**19 unittest tests passed.** The suite covers leaf ordering, cycles, ABI refusal, numeric bit edges,
alias/guard packing, exact float-bit comparison, incomplete output rejection,
source-blind prompt construction, known-function admission, retry feedback,
budget charging after interruption, resume without generation and identity drift.
The native timeout test is separate from mocked controller tests. Known-function
exchange and successful final integration were not exercised against a live
funcdb/fully covered original in this run.

The blockers are concrete:

1. **Recover ABI and host state.** Most parent functions need pointer layouts,
   suite callbacks, C++ object/vtable lifetimes, allocator contracts and exception
   behavior. Stored Toon signatures often say `undefined(void)` while decompiled
   C has parameters. Blindly generating pointer values is not a useful witness.
   Next: reuse recorded native context builders and verify recovered signatures
   before admitting parent functions.
2. **Close indirect calls and runtime/library dependencies.** A direct graph is
   insufficient for AE callbacks and C++ virtual dispatch. Next: resolve vtables
   and callback registrations through hub evidence, attach dynamic witnesses,
   and consume funcdb's verified wrapper exports once its API exists. Do not
   treat Ghidra library names as proof of Rust equivalence.
3. **Build the render adapter.** Declaration-compatible scaffolding does not
   marshal parameters into the generated contexts or implement ROI/pre-render
   behavior. Next: generate a reviewed owned-parameter snapshot and host adapter
   from recovered layouts, then run the final check on the integrated crate.
4. **Strengthen and reduce the corpus.** Add independent held-out random seeds,
   tolerance-neighbor floats, more sizes and structured state, plus value/shape
   shrinking with reproducibility checks. Current one-call reduction and fixed
   corpus can miss branches and do not prove arbitrary floating-state behavior.
5. **Tighten reproducibility and cost.** Pin model/version; remove unrelated CLI
   skill context through a supported isolated configuration; use smaller relevant
   import context (already implemented after the measured run). Add public kit
   output-root flags and an atomic hub comment-append/CAS API to eliminate the
   remaining concurrent-comment read/merge/write race.

Only the first nine leaf functions are qualified on these corpora. The orchestrator
preserves that boundary and leaves both overall ports `needs_human`.

Job N-antialias adds scoped button capture, target-directory control and an explicitly labelled reference bridge; see [N_ANTIALIAS.md](N_ANTIALIAS.md).
