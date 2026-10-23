status: blocked
summary:
- Both retained F49 workers have DirectionalBlur-specific resident watches, not configurable RadialBlur watches.
- All ten C49 inputs reproduce saved original output hashes on both workers (20/20); every trace has zero memory witnesses.
- Each trace explicitly reports both watches unhookable. No first divergent arithmetic stage can be established.
- Finite-input and missing-layer refusals remain unchanged; no production change is proposed.

facts:

FACT: Read C49/F49 reports, AGENT_GUIDE, GOTCHAS, compatibility plan and
RadialBlur ledger entries. Work is on `orch/C53-radial-nonfinite`. MAIN,
cached workers, emulator source, ledger, release gates and other plugins were
not modified. No worker rebuild, delegation, push or stash was performed.

FACT: The committed `tools/emulation/aexcompat_patches/build_F49.py` and the
retained worker source both hard-code `function_rva: Some(0x1ec0)` with RCX/RDX
rotation-input/output watches in `call_with_optional_trace`. The exposed
environment variables select the trace destination and capture size only.
V2 changes occurrence selection, not the target function. Worker hashes:

- F49: `44257f7a9244f351d1603d8796bc4b32433f24be053a07109cc152440e15c344`
- F49-v2: `25e57ac6b6ebbb26b68bb0631b9e1b8d8a7daf7290a03d9cd04e37cd87bb0c9d`

FACT: Ran the following sequential probe (one emulator process at a time):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/emulation/probe_radialblur_c53_trace.py --output orchestra/state/C53-radial-nonfinite/complete > orchestra/state/C53-radial-nonfinite/complete.log 2>&1
```

Exit 0. Seed1 indices 17/89/238/247 and seed105 indices
25/105/148/185/255/291 were regenerated and input-hash bound to C49.
All 20 traced renders completed with intact guards and clean sessions;
all 20 output hashes equal their saved successful C49 original references.
All 20 trace files exist, with zero memory witnesses and two unhookable
watch declarations each. The diagnostic is:
`no direct call site targets the function; checkpoint capture hooks direct call sites and the selector entry, not indirect calls`.

FACT: Original RadialBlur AEX SHA256 is
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
For seed1/index17, input SHA256 is
`d7a3e6039e53f6cfc8264f35240487b33519a3a61dd190fc8faa1fbb29d7015b`
and both workers produce the saved output SHA256
`e70c43ebde642036ed5bd6dd5a8132407f4cf063f932efecbb153a6b086a4a74`.
Full hashes, original statuses and complete traces for every input are committed
in `C53-evidence/trace-probe.json.gz`, with an uncompressed SHA256 manifest.
First Mac/AEX stage mismatch: unavailable, because no original stage was captured.
Zero output differences here compares traced originals to saved originals,
not Mac candidate conformance.

FACT: The initial probe exited 1 after four successful rows because seed105
stores its oracle under `oracle`, whereas seed1 uses `oracles.smart`.
The reader was corrected to support both existing report schemas; the complete
20-render run above supersedes it. The initial failure log is retained.

FACT: Missing-layer source inspection finds SmartRender explicitly refusing a
successful checkout returning null `noise_world` or null `noise_world->data`
with `smartrender-noise-world` (OLMRadialBlur.cpp:6268). C49's documented
host-only experiment still reached this refusal. This ticket did not establish
the original's null-world semantics from disassembly, and does not infer a
zero image or source substitution. That domain stays refused.

FACT: No arithmetic hypotheses were tested or promoted. No candidate build,
n300 admission campaign, corpus replay or sanitizer campaign was run: the
required original stage capture is unavailable and no admission was changed.
All started processes exited. No build trees were created; scratch at inspection
was 327,779 bytes, below 5 GiB. No permission rejection occurred.

inference:

INFERENCE: F49 supplies reusable SSE helpers but its retained trace interface
does not satisfy C53's prerequisite for RadialBlur. Changing arithmetic or
lifting the finite gate without those captures would repeat C44's unresolved
boundary. The worker brief disallows rebuilding retained workers unless the
ticket says so; C53 asks to reuse F49, so a separately authorized worker
extension is required. This is a tooling blocker, not evidence of an original
Windows bug or a numerical pass.

changed_files:
- `tools/emulation/probe_radialblur_c53_trace.py`
- `orchestra/reports/C53-radial-nonfinite.md`
- `orchestra/reports/C53-evidence/manifest.json`
- `orchestra/reports/C53-evidence/*.gz`

verify:

Use a fresh output directory (the probe intentionally rejects existing ones):

```sh
mkdir -p orchestra/state/C53-radial-nonfinite
PYTHONDONTWRITEBYTECODE=1 python3 tools/emulation/probe_radialblur_c53_trace.py --output orchestra/state/C53-radial-nonfinite/recheck > orchestra/state/C53-radial-nonfinite/recheck.log 2>&1
tail -1 orchestra/state/C53-radial-nonfinite/recheck.log
git diff --check
```

Expected: exit 0 and `{"cases": 20, "bound": 20, "witnesses": 0}`;
each trace reports both watches unhookable. Oracle timeout variability can
change completion counts and must not be called a numerical mismatch.

next:
- Authorize an F46-equivalent retained worker with configurable resident
  raw-input Smart watches for RadialBlur functions/instructions and full planes.
  Bind its output hashes to these ten originals before consuming captures.
- Resume first-divergence analysis with paired Mac stages, then implement only
  grounded general SSE semantics and run seed1/105/fresh n300, unchanged corpus,
  and ASan/UBSan before any finite-gate removal.
- Establish original missing-layer allocation/checkout and null-pointer branches
  from disassembly and trustworthy host captures before changing that refusal.
