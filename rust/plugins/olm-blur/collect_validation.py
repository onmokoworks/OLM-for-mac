#!/usr/bin/env python3
"""Collect completed P-blur runs without counting incomplete or different binaries."""
from pathlib import Path
from collections import Counter
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    runs = []
    for name in ['final-seed-20261112','final-seed-20261113','supplemental']:
        folder = HERE/'validation'/name
        s = json.loads((folder/'summary.json').read_text(encoding='utf-8'))
        assert s['complete'] and s['exit_code'] == 0, name
        for side in ['candidate','reference','harness','tool']:
            assert sha(s[side]['path']) == s[side]['sha256'], (name,side)
        plan = json.loads((folder/'cases.json').read_text(encoding='utf-8'))
        runs.append({'name':name,'seed':s.get('seed'),'cases_per_depth':s['cases'],
                     'random_per_depth':s['cases']-3 if name.startswith('final-seed') else 0,
                     'routes':s['routes'],'jobs':s['jobs'],'timeout_seconds':s['timeout_seconds'],
                     'scale_counts_per_depth':dict(Counter(c['downsample'] for c in plan)),
                     'legacy_counts_per_depth':dict(Counter(str(next((a['value'] for a in c['assignments'] if a['slot']==5),'default')) for c in plan)),
                     'summary_sha256':sha(folder/'summary.json'),
                     **{side:s[side] for side in ['candidate','reference','harness','tool']}})
    assert len({r['candidate']['sha256'] for r in runs}) == 1
    assert sum(r['random_per_depth'] for r in runs) >= 200
    assert len({r['seed'] for r in runs if r['seed'] is not None}) >= 2
    assert sha(r'D:/olm-rs-target/P-blur/release/olm_blur.dll') == runs[0]['candidate']['sha256']
    inventory = json.loads((HERE/'validation/final-inventory/summary.json').read_text(encoding='utf-8'))
    assert inventory['identical'] and not inventory['diff']
    pipl = json.loads((HERE/'pipl-comparison.json').read_text(encoding='utf-8'))
    assert pipl['identical']
    assert pipl['binaries'][1]['sha256'] == runs[0]['candidate']['sha256']
    assert inventory['candidate']['sha256'] == runs[0]['candidate']['sha256']
    env = json.loads((HERE/'validation/environment.json').read_text(encoding='utf-8'))
    assert sha(env['worker']['path']) == env['worker']['sha256']
    cleanup = json.loads((HERE/'validation/cleanup.json').read_text(encoding='utf-8'))
    assert cleanup['resolved'] and not cleanup['owned_live_processes']
    initial = json.loads((HERE/'validation/seed-20261112/summary.json').read_text(encoding='utf-8'))
    files = ['Cargo.toml','build.rs','src/lib.rs','src/algorithm.rs','src/ae.rs','src/ae_support.rs','src/reference_tests.rs','tests/reference.cpp','validate_supplemental.py','collect_validation.py']
    report = {'plugin':'OLMBlur','date':'2026-11-12','scope':'AEXCompat Windows x64 CPU; not native AE',
              'runs':runs,'inventory':inventory,'pipl':pipl,'environment':env,'cleanup':cleanup,
              'source_sha256':{f:sha(HERE/f) for f in files},
              'reference_source_sha256':{str(f.relative_to(ROOT)):sha(f) for f in sorted((ROOT/'core').glob('olmblur_*.cpp'))},
              'tests':{'passed':4,'cpp_cases':576,'thread_counts':[1,4],'comparisons':1152,'cpp_optimization':'O0: preserve source NaN operand order'},
              'pre_format_run':{'candidate':initial['candidate'],'seed':initial['seed'],'routes':initial['routes'],'included_in_final_counts':False},
              'hoisting_candidates':['fixed slider declaration and checkout','checkbox initial/default split','full-frame SmartPreRender union and extra-pixels flag','AEGP suite leases and visibility callback'],
              'new_external_dependencies':False}
    (HERE/'validation-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    total = sum(r['routes']['smart8']['exact'] for r in runs)
    random = sum(r['random_per_depth'] for r in runs)
    table = '\n'.join(f"| {r['name']} | {r['seed'] or 'targeted'} | {r['random_per_depth']} | {r['routes']['smart8']['exact']} | {r['routes']['smart16']['exact']} | {r['routes']['smart32']['exact']} |" for r in runs)
    ids = '\n'.join(f"- {side}: `{runs[0][side]['sha256']}`" for side in ['reference','candidate','harness','tool'])
    doc = f'''# OLMBlur Rust validation - P-blur

Windows x64, 2026-11-12. **{total} exact cases per Smart depth**, including
**{random} random cases per depth across two seeds**. Zero mismatches, reference
failures, timeouts or candidate failures. This is AEXCompat evidence, not native AE.

| Corpus | Seed | Random/depth | Smart8 exact | Smart16 exact | Smart32 CPU exact |
|---|---:|---:|---:|---:|---:|
{table}

Main runs cycle sizes `1x1,3x7,11x7,31x19,97x61` and downsample `1,1/2,1/4`.
The first three cases are explicit default/min/max assignments. Other cases sample
the full declared parameter ranges. Inputs contain partial alpha and hidden RGB.
Deep comparisons use native u16/f32 words, not preview PNGs. All runs use jobs=3,
process timeout 120 seconds and AEXCOMPAT_FRAME_DEADLINE_MS=120000 for both sides.

Supplemental: three untouched-default requests and three cropped demands
`[1,1,6,5]` within `11x7`, each cycling all three scales. This verifies full-frame
checkout union and RETURNS_EXTRA_PIXELS, not separately cropped output worlds.

## Identities

{ids}
- Worker: `{env['worker']['sha256']}`
- PiPL: `{pipl['binaries'][1]['pipl_sha256']}`; **294 bytes identical**.
- Final candidate: `validation/final-bin/OLMBlur.aex`.
- Build output: `D:/olm-rs-target/P-blur/release/olm_blur.dll`.

[validation-report.json](validation-report.json) retains complete paths, source
hashes, per-seed/depth/mode/scale counts and all exposed inventory comparisons.
Full inputs, requests, raw outputs and owned process PIDs are in ignored
`validation/`. The worker warns `source_newer_than_worker`; evidence binds the
recorded binary, not newer host source. Native UCRT FMA3 was measured enabled.

## Commands and results

From the repository root in PowerShell (use new output directories for reruns):

```powershell
$env:CARGO_TARGET_DIR='D:/olm-rs-target/P-blur'
cargo build --release -p olm-blur -j 2 --manifest-path rust/Cargo.toml
cargo test --release -p olm-blur -j 2 --manifest-path rust/Cargo.toml
$env:PYTHONUTF8='1'
$env:AEXCOMPAT_FRAME_DEADLINE_MS='120000'
$original='D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex/OLMBlur.aex'
$candidate=(Resolve-Path 'rust/plugins/olm-blur/validation/final-bin/OLMBlur.aex').Path
python rust/tools/oracle/olm_oracle.py inventory --reference $original --candidate $candidate --out rust/plugins/olm-blur/validation/final-inventory
python rust/tools/oracle/olm_oracle.py render --reference $original --candidate $candidate --cases 12 --seed 20261112 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --routes smart8,smart16,smart32 --timeout 120 --out rust/plugins/olm-blur/validation/final-seed-20261112
python rust/tools/oracle/olm_oracle.py render --reference $original --candidate $candidate --cases 203 --seed 20261113 --jobs 3 --sizes '1x1,3x7,11x7,31x19,97x61' --downsample '1,1/2,1/4' --routes smart8,smart16,smart32 --timeout 120 --out rust/plugins/olm-blur/validation/final-seed-20261113
python rust/plugins/olm-blur/validate_supplemental.py --reference $original --candidate $candidate --out rust/plugins/olm-blur/validation/supplemental
python rust/plugins/olm-blur/collect_validation.py
```

Build and tests pass: **4 tests**, including 576 tuples covering all six C++ workers
at Rust thread counts 1 and 4 (1152 comparisons). Cases include transparent barriers,
zero-radius previews, both biases, repeated/large radii, full-range u16, HDR/negative
float RGB, signed zero, infinity and distinct quiet/signaling NaN payloads. Other
assertions cover low-byte/word stores and odd-stride output padding. Rustfmt passes.
Inventory is identical across all exposed fields; PiPL was independently compared.

## Implementation and investigation

- Current `mac/OLMBlur` adapters and `core/olmblur_*` workers are authoritative.
  Older CLI/IR rounding notes were not substituted. RGB staging is unnormalized
  f32; integer writers use floorf(value+0.5), CVTTSS2SI and low-byte/word stores.
  PF16 does not saturate at nominal white 32768. PF32 stays float; alpha is preserved.
- Non-Legacy uses f32 powf decay, f64 pow radius, f32 radius materialization before
  truncation, and f32 expf coefficients. All UCRT calls use FMA mode. Denominator
  order is (sigma+sigma)*sigma. Smoothness discards its fixed-point fractional bits.
- Legacy preserves six carry partitions, backward exclusion of coordinate zero,
  asymmetric transparent writes and zero-radius pass execution. Production is
  serial; the pure non-Legacy API supports deterministic parallel rows.
- Optimized C++ reference compilation initially differed on mixed NaN payloads.
  `validation/fullworker-o2.asm` proves operand commutation: ADDSS has the new tap
  as destination and the old accumulator second, despite source add(accumulator,
  product). /Od retains source order and all 432 tuples match. Rust math was not
  changed. This test does not establish original-AEX nonfinite conformance.
- No original-AEX pixel mismatch required correction. Before validation, setup
  review corrected the alias to entryPointFunc, Legacy flags to 128 and version
  to 591872. The pre-format candidate passed 103 cases/depth; formatting changed
  its PE hash, so those results are excluded from the final binary counts above.
- A concurrent incomplete workspace member temporarily prevented Cargo parsing.
  Initial tests used an isolated manifest under owned validation/isolated. Final
  build/tests use the normal workspace; no other crate was edited.

## Preserved limits and remaining gaps

Smart worlds must have equal full-frame dimensions and zero origins. Extent hints
are not filtering clips. Public parameter bounds match C++. Small PF32 worlds
(both dimensions <=24) reject finite samples outside [-16,16]; nonfinite values
are admitted. Classic is default-tuple copy-only (Amount=5, Smoothness=100, Repeat=2),
with C++ bounds 4096x2160 and 3840*2160 pixels, and rejects PF32. It is not the AE
SmartFX dispatch route and is not counted as validated here.

No native AE or macOS build was run on this Windows machine. Smoothness hiding
mirrors the C++ callback but native UI remains unverified. PNG-promoted deep oracle
inputs do not cover arbitrary HDR/nonfinite native worlds; those have C++ kernel
tests only. Odd strides are unit-tested, not native AE qualified. Oracle jobs are
independent processes, not AE callback threads.

The oracle owns each child tree via a Windows Job Object, terminates residual
descendants and verifies ActiveProcesses=0 before returning. No background server,
AE application, browser, remote action, commit or installation was used. A final
PID audit checked 1,944 process records (1,427 unique PIDs): no owned process
remained. Reused PIDs were distinguished by creation time; an access-denied PID
was confirmed to be a newer svchost process and another had already exited.
Unrelated processes were left untouched. See validation/cleanup.json.

## Files and shared candidates

Only `rust/plugins/olm-blur/**` was authored: manifest/build script, algorithm,
AE adapter/local support, C++/Rust tests, validation scripts and evidence/report.
Cargo can automatically update the workspace lock. No new dependency beyond the
pilots was introduced. The OLM-internal math publication restriction is retained.

`src/ae_support.rs` locally extends olm-ae with fixed sliders, distinct checkbox
old-project value/default, full-bounds SmartPreRender union and extra-pixels flag,
and scope-bound AEGP suite/stream/effect cleanup. These are shared-hoisting
candidates. Shared crates were not edited; no additional UCRT wrapper was needed.
'''
    (HERE/'VALIDATION.md').write_text(doc,encoding='utf-8')
    print(f'Collected {total} exact cases/depth; {random} random cases/depth.')

if __name__ == '__main__':
    main()
