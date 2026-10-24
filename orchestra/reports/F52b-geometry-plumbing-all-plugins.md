status: blocked
summary:
- Added a versioned realistic geometry sampler, crop/shrink support and embedded/procedural corpus replay.
- Added --geometry realistic, with explicit rejection until a candidate host qualifies the geometry contract; no adapter is enabled yet.
- Default corpus reconstruction is identical for 769/769 saved cases; rendered-output replay was not run.
- Retained F52 oracle does not negotiate expanded output allocation; rebuilding reference workers requires explicit ticket authorization.
- Candidate/bundle plumbing and all ten requested seed-1 n100 measurements remain incomplete. This is not completion of F52b.

facts:

Commands run from this worktree:

1. `OLM_FUZZ_TEST_SCRATCH="$PWD/orchestra/state/F52b-geometry-plumbing-all-plugins/tests" TMPDIR="$PWD/orchestra/state/F52b-geometry-plumbing-all-plugins" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fuzz -p 'test_*.py'`
   Final result: **39 tests, OK, 2 skipped**, 7.469 seconds. The sampler test
   generates seed 1 / indices 0–99 for each of the ten adapters, including
   RadialBlur's independent adapter. These are **1,000 generated inputs, not
   emulator comparisons**. Coverage assertions include all six downsample
   choices, six byte-padding choices, four aspects, non-full request rectangles,
   valid crops, a real shrink-driver run, and both corpus storage forms.
   [Log](F52b-evidence/tests.log).
2. `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/verify_F52b.py`
   **769 reconstructed, 769 identical, 0 rendered** against `core.py` at starting
   commit `22f8f8023645f6299abe6a19f2f596eae7157148`. Compares the entire case,
   including bytes and metadata, after loading saved reduction operations.
   Path/input-hash manifest SHA-256:
   `198262d6a0f93c22fd6a28704e732a65f451a7c68fa4bcca212d4af1b5429b7d`.
   [Evidence](F52b-evidence/default-reconstruction.json).
3. `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/probe_F52b_boundary.py`
   Original ColorKey Smart, PF8 1×1: request `[0,0,1,1]` returns 4 bytes,
   SHA-256 `c380b89b8bd6a0f2c08f378493dc412d7aa1b0cae4b2074358ac3cfdd6220c22`.
   Request `[0,0,2,1]` returns process status 2, diagnostic
   `aex_guest_error: rectangle outside sampled world`, and no output bytes.
   Worker hash is the retained F52 hash:
   `1be0cb14f6e68ab9276ef37be3a381aae9fb0306914987eb91e1a9d23dd94f4b`.
   Initial probe assertion expected a later validation message; corrected it to
   the observed earlier geometry validation diagnostic and reran successfully.
   [Evidence](F52b-evidence/oracle-boundary.json).
4. `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/run.py --plugin radialblur --seed 1 --n 100 --jobs 1 --geometry realistic --scratch "$PWD/orchestra/state/F52b-geometry-plumbing-all-plugins/check" --report "$PWD/orchestra/state/F52b-geometry-plumbing-all-plugins/admission.json" --corpus "$PWD/orchestra/state/F52b-geometry-plumbing-all-plugins/corpus"`
   Exit **2**, `setup_error`, `radialblur: host has not qualified realistic-v1 geometry`.
   No build or render occurred. This verifies the new host-capability check;
   it is **not** a Mac plugin refusal and must not be counted as R.
5. `git diff --check`: passed. Scratch was below 1 MiB; no reference worker,
   bundle, plugin source, MAIN file, ledger or release gate was modified.

Source inspection facts:

- F52 handoff and `tools/emulation/aexcompat_patches/README-F52.md` explicitly
  exclude expanded output allocation negotiated by PreRender.
- Read-only retained source
  `/Users/onmk/.cache/olm-emu/src-F52/reference-guest/crates/aex-guest-worker/src/classic.rs`:
  output-world construction at line 2337 precedes the Smart lifecycle;
  PreRender at lines 3274–3297 reads its output but returns only error/flags to
  the lifecycle. This path does not reallocate the primary output from result_rect.
- The runtime probe above establishes the separate **request-rectangle** boundary;
  it does not equate request_rect with a plugin's negotiated result_rect.
- `adapters/olmsmoother.py` and `adapters/olmsmoother2.py` build their shim hosts
  directly, bypassing PublicAdapter.geometry_host. Smoother2's shim PF_InData
  (`cli/OLMSmoother2/shim/OLMSmoother2.h:139`) has downsample but no pixel aspect
  or extent member. Simply setting shared environment variables is insufficient.
- F51's standalone host rounds input padding to pixel alignment and fixes output
  stride/dimensions. F47d also receives an already allocated destination.

E/M/R/U and refusal tags: **not measured** for ColorKeep, DistanceGradation,
KiraKira, RadialBlur, ToonDilate, Smoother2, Smoother Classic, Blur, ColorKey or
DirectionalBlur. There are no new plugin mismatch/refusal witnesses or downsample
disassembly findings from this ticket. Do not substitute F52's narrower campaign
counts for the requested full realistic campaign. The oracle-boundary rejection
is a host limitation, not a faithful original PF-error refusal.

inference:

- Completing the negotiated-output comparison needs an explicitly authorized
  extension/qualification of the retained reference worker, in addition to
  candidate host changes. The worker brief prohibits rebuilding a reference
  worker unless the ticket says so; this ticket specifically requests candidate
  and bundle-host plumbing. I did not infer authorization for an oracle rebuild.
- Fixed-world padding/extent/aspect candidate work could proceed independently;
  that implementation is unfinished here, not proven impossible by the oracle
  boundary. The blocking issue prevents claiming the complete requested contract.
- No two-hypothesis numerical investigation was attempted. The numerical stop
  rule was not invoked. This handoff stops at an unqualified host contract.

changed_files:

- `tools/fuzz/geometry.py`: deterministic secondary RNG, sampled-world crop,
  fixed-point point scaling, byte padding, extent/request, aspect, crop consistency.
  Output geometry is intentionally not invented from the input request.
- `tools/fuzz/core.py`: preserve sampler version in procedural corpus and update
  geometry metadata when cropping; default cases pass through unchanged.
- `tools/fuzz/run.py`: opt-in flag and explicit host qualification check for
  generation/replay. No adapter declares qualification yet.
- `tools/fuzz/test_geometry.py`
- `tools/fuzz/verify_F52b.py`
- `tools/fuzz/probe_F52b_boundary.py`
- This report and `orchestra/reports/F52b-evidence/`.

verify:

Run commands 1–3 above; expect **39 tests with 2 skips**, **769/769 identical
reconstructions**, and **one successful 1×1 render plus one expanded-request
host rejection**, respectively. Command 4 is an intentional negative check:
expect exit 2 before rendering, not an E/M/R/U campaign. Run `git diff --check`
for whitespace validation. No saved expected result is changed.

next:

1. Explicitly authorize an oracle output-negotiation extension in an isolated
   cache build, retaining the default worker, with guard/stride/origin checks and
   a durable registered artifact. Define packed output serialization and compare
   negotiated dimensions/origins before comparing samples.
2. Complete source-host and F47d/F51 geometry plumbing, including the two shim
   hosts and RadialBlur's independent path; qualify each before declaring
   `geometry_samplers = ('realistic-v1',)` on its adapter. Do not enable the flag
   merely to bypass the qualification check.
3. Run all ten seed-1 n100 campaigns serially, classify original errors separately
   from emulator limitations, retain first witnesses/tags and original downsample
   disassembly pointers, and perform actual default rendered-output replay.
