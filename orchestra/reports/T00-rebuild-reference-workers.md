status: partial
summary: >
  Rebuilt the whole RadialBlur reference-worker chain from the committed recipes
  into the persistent cache /Users/onmk/.cache/olm-emu (3.4 GiB logical, 9 links).
  All source-file manifests match the recorded reports exactly (only the build
  JSON files differ). No worker_sha256 matches the recorded value: the recorded
  hashes embed the original absolute build path and AEXCOMPAT_BUILD_REVISION, so a
  relocated rebuild cannot be byte-identical. The offset deadline-bound worker and
  its offset_bound alias exist; no distinct committed offset_bound recipe exists.

facts:
  root:
    - repo: /Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat
    - branch: issue1584-signal-ui, commit bd878da64dc6e91a24a78c6b00fce30f783dc3b0, subdir guest
      (found by scanning refs for the recorded imports.rs sha e96b91a4...; only this branch matched
       imports.rs e96b91a4... and callbacks.rs 2ac0473d...)
    - imported via `git archive bd878da... guest | tar -x --strip-components=1` into
      /Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da (never built in place)
  chain_rebuilt (parent -> child, all under /Users/onmk/.cache/olm-emu):
    - radial_frozen_reference_bd878da          worker 544ff209d11b...  (recipe: cargo build, rust 1.93.1, AEXCOMPAT_BUILD_REVISION=bd878da64dc6)
    - radial_controlled_reference_20261001     worker a67383ee4e6d...  (build_radialblur_controlled_math_worker_20261001.py)
    - radial_typed_trace_reference_20261001    worker 1b965a02a138...  (build_radialblur_typed_trace_worker_20261001.py)
    - radial_axis_reference_20261001           worker f45db6a215bb...  (build_radialblur_axis_reference_20261001.py)
    - radial_doublecast_reference_20261001     worker f59d30f4c404...  (build_radialblur_doublecast_reference_20261001.py)
    - radial_windows_reference_v2_20261001     worker 16ab2412c00b...  (build_radialblur_readonly_windows_reference_20261001.py)
    - radial_noop_highdepth_reference_20261002 worker 9ac2c86cb707...  (build_radialblur_noop_reference_20261002.py)
    - radial_offset_reference_20261002         worker 93622cbc412f...  (build_radialblur_offset_reference_20261002.py, 20s -> 120s deadline)
    - radial_offset_bound_reference_20261002   alias of radial_offset_reference_20261002 (no distinct committed recipe)
  source_manifest_comparison (local vs recorded reports):
    - frozen base vs reports/radialblur_controlled_reference_build_20261001.json.base_source_files_sha256:
      436/436 files equal, 0 mismatches; imports.rs and callbacks.rs patches equal to recorded.
    - typed parent manifest vs reports/radialblur_typed_trace_reference_build_20261001.json: 437 files,
      1 mismatch = controlled-reference-build.json only; main_base/main_patched hashes equal.
    - axis: 438 files, mismatches = controlled/typed build JSONs only; callback_patched equal.
    - doublecast: 439 files, mismatches = 3 earlier build JSONs only; callback_patched/trace_patched equal.
    - windows: 440 files, mismatches = 4 earlier build JSONs only; callback_sha256 equal.
    - noop: 441 files, mismatches = 5 earlier build JSONs only; `changed` block equal.
  hash_mismatch_evidence:
    - `strings <worker>` shows absolute path /Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/...
      embedded in the release binary; build.rs also embeds AEXCOMPAT_BUILD_REVISION
      (git rev-parse --short=12 HEAD, or "unknown" outside a git tree).
    - same source, different build directory / remap path gives different worker sha256
      (e.g. frozen source alone produced 5476d29c..., 544ff209... with revision env,
      121a4370.../3e2a49a8.../4ff5fad6.../9651e0d6... under path remaps).
    - attempt to reproduce the recorded hashes by remapping to the documented /tmp names and/or
      setting AEXCOMPAT_BUILD_REVISION did not match (windows remap attempts: a60c820c..., a71b1200...;
      controlled remap attempt: 1666e8ef...). Toolchain default is now rust 1.95.0 while the repo pins 1.93.1.
  offset_evidence:
    - committed offset recipe asserts parent = windows build and changes only
      crates/aex-guest-worker/src/x64.rs (TIMEOUT_MICROSECONDS 20_000_000 -> 120_000_000).
      probe_radialblur_offset_20261002.py:179-193 requires `set(binding['changed'])=={x64.rs}` and
      `binding['parent_worker_sha256']==previous['window_worker_sha256']` (windows, not noop).
    - ticket chain noop -> offset -> offset_bound is not backed by any committed recipe/patch;
      no committed report records an offset worker_sha256 at all.

inference:
    - The root source is almost certainly issue1584-signal-ui@bd878da: every base source hash matches.
    - The recorded worker_sha256 values are path/toolchain/revision-specific and cannot be
      reproduced outside the original build directories; this is build-environment drift,
      not a source difference.
    - The "offset_bound" link is the same deadline-bound offset worker; treating it as a distinct
      artifact would require inventing a recipe.

changed_files:
  - orchestra/reports/T00-rebuild-reference-workers.md
  - orchestra/reports/emu_index.json
  - orchestra/reports/T00_build_controlled_local.py
  (cache, outside repo: /Users/onmk/.cache/olm-emu/INDEX.json + 9 link dirs)

verify:
  - python3 - <<'PY'  (expect all True)
    import json,hashlib;from pathlib import Path
    C=Path('/Users/onmk/.cache/olm-emu')
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    d=json.load(open(C/'INDEX.json'))
    print(all((C/l['name']/'target/release/aex-guest-worker').is_file() for l in d['links']))
    print(sha(C/'radial_offset_reference_20261002/target/release/aex-guest-worker')==sha(C/'radial_offset_bound_reference_20261002/target/release/aex-guest-worker'))
    PY
  - shasum -a 256 /Users/onmk/.cache/olm-emu/*/target/release/aex-guest-worker
    (expect the 8 distinct hashes in INDEX.json; offset and offset_bound share one)
  - python3 orchestra/reports/T00_build_controlled_local.py  (rebuilds controlled link only; expect a67383ee4e6d...)

next:
  - If probes need exact recorded hashes, rebuild at the original absolute paths (forbidden /tmp) or
    add a deterministic --remap-path-prefix + AEXCOMPAT_BUILD_REVISION convention to the recipes.
  - Confirm with T01 whether radial_offset_reference_20261002/radial_offset_bound_reference_20261002
    were one artifact; if two, a recipe/patch for the bound child must be recovered.
  - Rebuild corrupted references: tests/test_radialblur_noop_20261002.py and
    probe_radialblur_strength_*_20261002.py still hardcode /tmp/radial_windows_reference_v2_20261001.
disk:
  - /Users/onmk/.cache/olm-emu: 3.4 GiB logical (9 APFS clones); system reported ~2 GiB data growth.
