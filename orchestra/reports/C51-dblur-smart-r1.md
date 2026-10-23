status: blocked
summary:
- Measured 600 cases: seed 1 Smart 296 exact / 0 mismatch / 2 refusal / 2 uncompared; seed 104 294 / 0 / 2 / 4.
- All four refusals are nonfinite PF32 inputs; no production change or cluster closure is claimed.
- Two scratch admission hypotheses fail on all four witnesses against F46; O2 and ASan/UBSan agree.
- Existing paired traces still do not bind to F46 final output; no trustworthy new first-divergent-stage boundary was obtained.
- Stopped under the two-refuted-hypotheses rule; saved corpus replay remains 83/83 unchanged.

facts:

FACT: Base `59b4273d640e30d23fc76ea58374c59874af609c`, branch
`orch/C51-dblur-smart-r1`. Consulted AGENT_GUIDE, the DirectionalBlur ledger
row, compatibility plan, GOTCHAS, T10, C02/C09/C18/C25/C30/C36/C45,
F10/F12/F29 and S01 evidence. No production source, corpus expectation, MAIN,
external emulator source, cached worker, other plugin, release gate or ledger
was modified. No worker rebuild, push, stash, history rewrite or permission
rejection occurred.

FACT: Numerical scope is original CPU AEX Smart in Unicorn versus public Mac
EffectMain in the SDK fake host, typed ARGB bytes, full-frame origin zero.
This is not native AE or Windows validation. Worker:
`/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker`, SHA256
`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
AEX SHA256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
Complete compressed campaign, experiment, trace and replay reports are in
`orchestra/reports/C51-evidence/`; `manifest.json` hashes their decompressed
bytes. Reports include controls, input/output hashes, first mismatches,
source/build provenance and exact compiler argument arrays.

FACT: Both requested campaigns completed 300/300, exit 0, jobs 1,
shrink-attempts 0, default 10-second per-call timeout. E/M/R/U denotes Smart
exact/mismatch/refusal/uncompared. No production edits followed these baselines.

| Set | Before E/M/R/U | Final E/M/R/U |
|---|---:|---:|
| seed 1 n300 | 296/0/2/2 | unchanged source |
| seed 104 n300 | 294/0/2/4 | unchanged source |
| saved corpus | 83/83 saved results | 83/83 saved results, new replay |

The archived S01 seed104 report records 279/0/19/2, with 3 oracle budgets
(one overlapping a refusal). Those historical results precede this ticket;
this ticket does not claim their improvement as its own. Current seed1 oracle
budgets are indices 274/289; seed104 budgets are 20/84/227/296. Timing varies
with machine load. All current refusing cases have completed AEX Smart outputs.
Both measured Classic routes have 4 exact / 294 mismatch / 2 refusal, retained
as diagnostics outside this Smart ticket.

FACT: Largest remaining refusal cluster is the `pf32-nonfinite-input` guard:
seed1 indices 109/299 and seed104 indices 137/271. The new reproducer selects
all refusals from the completed campaign reports, asserts the nonfinite profile
and completed oracle, regenerates inputs, and binds input and reference hashes.
It reuses C30's gate bypass and C36's rotation correction without production
edits. These are rechecks of previously rejected ideas against current F46 and
fresh seed104 witnesses, not newly discovered algorithms.

Hypothesis 1: current arithmetic permits admission if only the finite-input
guard is removed. Hypothesis 2: adding operand-aware generated-default-NaN
correction to rotation's four arithmetic helpers suffices for admission.
Both are refuted: zero exact admissions in each experiment.

| Seed:index | Gate bypass differing bytes/words | Rotation correction bytes/words | First mismatch after correction: byte; AEX → candidate LE word |
|---|---:|---:|---|
| 1:109 | 2808/969 | 2680/880 | 6; `0000803f` → `0000c0ff` |
| 1:299 | 1919/728 | 1834/634 | 20; `0000803f` → `4523c17f` |
| 104:137 | 1044/360 | 1004/320 | 4; `0000803f` → `4523c17f` |
| 104:271 | 73/30 | 70/27 | 6; `0000803f` → `0000c0ff` |

FACT: Probe exits 0 because its measurement assertions pass, not because
rendered pixels agree. Each of the 8 experiment/witness pairs agrees between
O2 and ASan/UBSan; flags include `-fsanitize=address,undefined` and
`-fno-sanitize-recover=all`, halt-on-error enabled, leak detection disabled.
No sanitizer diagnostic occurred. This is bounded witness safety, not broad
nonfinite correctness or a full production sanitizer regression.

FACT: Existing paired trace command exits 0 with the explicit diagnostic
`--allow-fixture-difference`. For seed1 109/299, populated planes match and
rotation differs by 440/310 float words; first offsets 2084/1824 contain
fixture `0000c0ff` versus Mac `0000c07f`. However fixture final outputs differ
from F46 by 421/312 bytes, first byte 32 for both. The fixture uses native-f32
math substitutes and the Python Unicorn library; it is not a F46-bound trace.
These reproduce the C36 boundary, not a new authoritative first divergence.
No numerical correction is justified from those traces alone.

FACT: Saved corpus replay completed 83 cases, exit 0, `replay_matches_saved=true`.
It uses each corpus record's hash-bound worker and timeout, rather than silently
rebinding older evidence to F46. No corpus file requires rebaselining. Production
source identity preserves base-exact behavior; no new broad sanitizer claim is
made. All started processes completed. Temporary build directories were cleaned
by their context managers; only logs/reports and small scratch corpus remain,
well below 5 GiB. `git diff --check` passes.

inference:

INFERENCE: Current residuals do not support either general nonfinite admission
rule. The generation-sign correction reduces differences but leaves payload,
selection and downstream behavior unresolved. The existing fixture's output
binding failure prevents treating its stage values as the F46 first divergence.
Two admission hypotheses are refuted without a new trustworthy intermediate
boundary, so the required stop condition applies. Zero clusters are closed.
No new original-OLM undefined-read bug or deterministic-semantics rule was proven.

changed_files:
- `tools/fuzz/probe_directionalblur_c51_nonfinite.py`
- `orchestra/reports/C51-evidence/{seed1,seed104,probe,stages,replay}.json.gz`
- `orchestra/reports/C51-evidence/manifest.json`
- `orchestra/reports/C51-dblur-smart-r1.md`

verify:

Run sequentially from the worktree. Commands below correspond to the measured
runs; all exited 0. Expected campaign counts, probe differences and 83/83 corpus
results are above (oracle timeouts may vary). The trace is explicitly diagnostic
and is expected to fail final-output equivalence, despite process exit 0.

```sh
S="$PWD/orchestra/state/C51-dblur-smart-r1"
W=/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 1 --scratch "$S/seed1" --report "$S/seed1.json" --corpus "$S/corpus1" --shrink-attempts 0 > "$S/seed1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 104 --jobs 1 --scratch "$S/seed104" --report "$S/seed104.json" --corpus "$S/corpus104" --shrink-attempts 0 > "$S/seed104.log" 2>&1
python3 tools/fuzz/probe_directionalblur_c51_nonfinite.py --campaigns "$S/seed1.json" "$S/seed104.json" --worker "$W" --scratch "$S/probe" --report "$S/probe.json" > "$S/probe.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --indices 109 299 --nonfinite-off --expf-leaf native-f32 --powf-leaf native-f32 --allow-fixture-difference --scratch "$S/stages" --worker "$W" --report "$S/stages.json" > "$S/stages.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --replay tests/fuzz_corpus/olmdirectionalblur --jobs 1 --scratch "$S/replay" --report "$S/replay.json" > "$S/replay.log" 2>&1
git diff --check
```

next:
- Separate harness ticket: expose paired stage capture from the exact F46 worker,
  or restore a Python fixture with the same SSE NaN and UCRT semantics and prove
  complete output binding first. This ticket does not authorize rebuilding workers.
- Once binding is restored, use all four retained inputs to locate the first
  arithmetic/selection divergence. Keep the finite-input gate until seed1/fresh
  seed, preserved-exact corpus and sanitizer acceptance pass.
- Oracle-budget witnesses remain uncompared; they are not Mac mismatches.
