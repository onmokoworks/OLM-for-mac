status: blocked
summary:
- Built and registered the authorized C53b-derived R08 worker with 64 MiB read-only snapshots; deleted its build tree.
- Fixture165: six full-size planes and final output match current Mac exactly; both traced finals equal both F46 finals.
- Refreshed only those six proven plane pins. The complete fixture165 command passes, including its unchanged sampler/writeback checks.
- Complete 18-command closure remains unresolved: additional legacy noise checkpoints cannot be armed through either resident watch selector.
- Stopped further capture investigation under the two-refuted-hypotheses rule; no production changes or release-gate edits.

facts:

The worker is installed at `~/.cache/olm-emu/worker-R08-trace/aex-guest-worker`, registered under the INDEX lock. Its SHA-256 is `c56b76ed1400b9a9cf835271f1f77dc36fccee02325b727ff8e1d666bc1878f5`. Parent C53b SHA-256: `df51edc461ee13ae826c94e62b29c17b813181ef1c2719388e4d9faf180099a2`. The patch changes only the two snapshot-size constants/validation bounds from 16 MiB to 64 MiB. The retained source is `~/.cache/olm-emu/src-R08/reference-guest`; `build-R08` was deleted. External `04_Tools/AEXCompat*` and MAIN were not edited.

Commands/results:

- `python3 tools/emulation/aexcompat_patches/build_R08.py`: exit0; offline/locked Cargo build with one job. Parent source manifest verified before copying. Build admission memory free: 52%.
- `bash scripts/setup_ae_sdk_links.sh`: exit0.
- MAIN venv `python3 -B orchestra/reports/R08-fullsize.py`: exit0. Four original-AEX sessions: twice F46, twice R08 with watches enabled. All return `ok`, intact guards and clean sessions. Both traces have no truncation, dropped witnesses or unhookable watches; all six selected snapshots have complete lengths and valid hashes. Traces are reduced to compressed raw planes and metadata after validation, one trace at a time.
- Original AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`; source ARGB8 SHA-256: `56e34962532d6917ee72a11cc8ee9de81ed6d1d891d48e21876c807ff20bb255`.
- F46 SHA-256: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`. All four 8,294,400-byte final outputs have SHA-256 `cb39306e0e340bfa121e5ea55c9e1b43f87696237b4d6c855a47ce09dba188fc`.
- Current Mac comparison: **six intermediate planes plus final output; 121,564,800 bytes per repeat; zero differing bytes; first mismatch null**. RGBA planes are 31,795,200 bytes each; scalar planes 7,948,800 bytes; eligibility 1,987,200 bytes. Both original repeats are identical. Per-plane hashes and production source binding are in `R08-results.json`.
- `python3 orchestra/reports/R08-refresh-fullsize.py`: exit0, independently checks both original repeats and Mac bytes before writing fixture pins. The old fixture remains intact. Only the full-size command's six-plane fixture path changes; its final-output reference and every coordinate/sampler/writeback assertion remain intact.
- The complete full-size command was run with only REPORT/TMP destinations redirected into scratch: exit0, harness status `native_exact`. This is the retained harness's bounded label, not a new real-AE or Windows-host run.
- Legacy-to-fresh drift: accumulator **1,801,887 differing bytes**, first byte **0**, old `119`, fresh/Mac `120`; normalized plane **95,827 differing bytes**, first byte **2,167,728**, old `88`, fresh/Mac `89`. Polar, source scalar, eligibility and maximum-alpha hashes are unchanged. `legacy-plane-drift.json` in the archive records complete hashes. These are old-reference differences, not fresh-original versus Mac mismatches.
- MAIN venv `python3 -B orchestra/reports/R08-extra-plane-capability.py`: exit0 denotes two expected failed checkpoint-admission strategies, not successful plane capture. On record153's retained typed source, `instruction_rva=0x8162` reports “rva is not a call or jump instruction in an executable section”; `function_rva=0x8162` reports “no direct call site targets the function”. Both sessions complete cleanly with 1,008 output bytes, the same final SHA-256 `e195b7c6bf0f162bd0c575e9e428d9d084e1ea4e6aa1164c9dbf5f55b6d201b2`, and **zero memory witnesses**. Neither yields a new noise boundary value. The legacy PF16/PF32 capture uses this post-noise checkpoint (PF32 owner) and RBX-relative noise fields; RBX is also absent from the resident schema. The probes use supported RCX to isolate hook admission from register admission.
- `R08-run-legacy.py` reruns the original 18 modules sequentially with report/temporary destinations redirected, preserving assertions. All **18** commands completed: **1 PASS (165), 17 FAIL**, no timeout. The runner exits0 after recording each command result; it does not treat command failures as passes. Per-command durations/exit codes and logs are retained.
- `R08-package.py`: exit0; archive integrity verified for all 85 members. Archive size 5,883,152 bytes, SHA-256 `45f4de8ba46bed8dedcda277cc7a07101592690362e4abc9812312d6df442369`.
- Python AST parsing and `git diff --check`: pass. No worker subprocess is left running. Scratch stayed below 5 GiB; sampled free memory stayed at least 43%. No reference worker rebuild beyond the authorized R08 child; no production, release gate, ledger, or other-plugin code changes.

inference:

Full-size165's old accumulator/normalization pins reflect reference arithmetic drift: the fresh original repeats and unchanged Mac agree at every byte, and all four complete final outputs agree. Refreshing those measured pins is justified and closes fixture165's prior failure.

The larger buffer resolves the R06 full-size limitation, but it does not turn the resident direct-call tracer into the arbitrary-instruction tracer used by the older multi-case Python harnesses. The remaining commands still generate their references through the old loader; changing only their hash constants would not repair the observed computed-plane mismatches. Complete reference-producer migration, additional cases/diagnostic planes and negative assertions remain unverified by this ticket. The two failed selector probes establish only that the existing selectors cannot arm this legacy checkpoint; they do **not** prove that no equivalent caller-boundary capture is possible. No third workaround was attempted after the stop condition.

changed_files:

- `tools/emulation/aexcompat_patches/build_R08.py`, `R08-snapshot-capacity.patch`, `R08-snapshot-capacity.md`.
- `tools/emulation/test_olmradialblur_case0010_rotation_mac_production_planes_20260805.py`: proven intermediate fixture binding only; final reference preserved.
- `refs/fixtures/olmradialblur_R08_fullsize_20261024/`: six compressed planes and provenance manifest.
- `orchestra/reports/R08-{fullsize,refresh-fullsize,extra-plane-capability,run-legacy,package}.py`.
- `orchestra/reports/R08-results.json`, `R08-evidence.tar.xz`, `R08-artifact-manifest.json`, this report.

verify:

Use the installed worker (no rebuild required):

```sh
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/orchestra/state/R08-radial-fullsize-trace"
export TMP="$TMPDIR" TEMP="$TMPDIR"
mkdir -p "$TMPDIR"
PY="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3"
bash scripts/setup_ae_sdk_links.sh
"$PY" -B orchestra/reports/R08-fullsize.py > "$TMPDIR/fullsize.log" 2>&1
python3 orchestra/reports/R08-refresh-fullsize.py
"$PY" -B orchestra/reports/R08-run-legacy.py --index 165 > "$TMPDIR/recheck165.log" 2>&1
"$PY" -B orchestra/reports/R08-extra-plane-capability.py > "$TMPDIR/extra-plane-capability.log" 2>&1
"$PY" -B orchestra/reports/R08-run-legacy.py > "$TMPDIR/legacy.log" 2>&1
git diff --check
```

Expected: four equal full-size finals, six exact intermediate planes, no snapshot truncation; two zero-witness checkpoint-admission failures; fixture165 passes. The other commands remain unresolved, not promoted. The replay wrapper preserves their assertions and records each exit code. Run commands sequentially and check `memory_pressure` remains at least 30% free.

Offline evidence integrity:

```sh
python3 - <<'PY'
import hashlib,json,tarfile
from pathlib import Path
p=Path('orchestra/reports'); m=json.loads((p/'R08-artifact-manifest.json').read_text())
with (p/m['archive']).open('rb') as f:
    assert hashlib.file_digest(f,'sha256').hexdigest()==m['sha256']
with tarfile.open(p/m['archive']) as t:
    assert len(t.getmembers())==len(m['files'])
    for row in m['files']:
        with t.extractfile(row['path']) as f:
            assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
r=json.loads((p/'R08-results.json').read_text())
assert len(r['fullsize']['runs'])==4
assert len({x['sha256'] for x in r['fullsize']['runs']})==1
assert all(x['different_bytes']==0 and x['repeat_identical'] for x in r['fullsize']['planes'].values())
assert r['fullsize_command_status']=='native_exact'
print('R08 full-size evidence intact; broader closure remains blocked')
PY
```

next:

Follow up the remaining 17 commands' complete reference transport: resolve the post-noise/extra diagnostic checkpoints through an equivalent supported boundary, or explicitly authorize an arbitrary-instruction/register trace extension. Capture each remaining tuple/plane twice, bind finals to F46, compare with Mac, then migrate the legacy reference producers and refresh only proven pins. Preserve all negative assertions. This ticket does not claim all 18 commands or all their required planes are closed.
