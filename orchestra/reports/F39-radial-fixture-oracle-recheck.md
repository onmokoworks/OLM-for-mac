status: blocked
summary:
- Replayed the F36 first-failing witness for each of all 18 commands with the pinned F32 original-AEX worker.
- Final pixels: 14 A (oracle drift), 4 C (intermediate-only); F32 equals Mac HEAD in all 18. No B found in these witnesses.
- Committed 14 provisional F32 final fixtures with provenance; a companion test freshly verifies both F32 and Mac Smart.
- Full legacy command rebinding is incomplete: F32 cannot trace these exact typed inputs through its PNG-only trace interface.
- Kept every old fixture/assertion, production source, release gate, and ledger unchanged; no worker rebuilt.

facts:

Candidate revision: `3781f6320be08bb475dbbc39d2cb192808ce7c40`.
Original AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
F32 worker SHA-256: `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`.
All original-AEX session replays reported intact guards and clean sessions.
`F39-evidence.json` records all controls, input hashes, output hashes, byte counts,
first mismatches, and legacy plane comparisons. Source assets use F36's resolver.

The table compares **packed visible final bytes**, so offsets exclude row padding.
Every F32-versus-Mac comparison has zero differing bytes. These are representative
first-failing witnesses, not a claim that every case in the multi-case legacy
commands has been re-adjudicated.

| Command | Witness | Class | F32 vs old differing bytes | First byte |
|---:|---|:---:|---:|---:|
| 152 | Rotation PF32 Size1 | A | 83 | 4 |
| 153 | Rotation PF32 NV0 | A | 83 | 4 |
| 155 | Rotation PF32 Ratio2 Angle0 | A | 82 | 24 |
| 156 | Same, 32x18 | A | 674 | 8 |
| 157 | Rotation PF32 Strength5 NV25 | A | 85 | 4 |
| 158 | Rotation PF32 OffsetMode3 Offset2 NV25 | A | 4 | 500 |
| 159 | Zoom PF32 Inner50 NV25 | A | 48 | 4 |
| 165 | Full 1920x1080 case0010 PF8 | C | 0 | — |
| 167 | Rotation PF16 neutral | A | 2 | 250 |
| 168 | Rotation PF32 neutral | A | 83 | 4 |
| 169 | Rotation PF32 OuterFade50 | A | 102 | 12 |
| 170 | Rotation PF32 OuterFade50 NV25 | A | 50 | 8 |
| 171 | Rotation PF32 Strength5 | A | 9 | 60 |
| 172 | Rotation PF16 Strength5 | C | 0 | — |
| 174 | Zoom PF16 Strength5 | C | 0 | — |
| 178 | Rotation PF32 OffsetMode3 Offset3 | A | 1 | 664 |
| 179 | Rotation PF32 OffsetMode3 Offset4 | A | 41 | 36 |
| 181 | Rotation PF16 OffsetMode3 Offset3 | C | 0 | — |

The old direct-owner captures were regenerated without calling their `main()`
functions, so they could not overwrite retained fixtures. Their padded output
hashes match retained binary fixtures or historical reports (paths in evidence;
159 is bound by the F36 report). The F32 session protocol accepts packed input,
so the AEX comparison excludes padding. Mac direct harnesses retain original
padded worlds; fresh companion verification also checks packed public Smart.
The 14 new expected outputs come exclusively from saved F32 AEX bytes.

Class C details, measured against retained/legacy AEX captures:

- 165: accumulation differs in 1,801,691 float words, first word 0; normalized
  polar differs in 95,441 words, first word 541932. Polar, eligibility,
  source-scalar and max-alpha remain exact. Final SHA-256 remains
  `cb39306e0e340bfa121e5ea55c9e1b43f87696237b4d6c855a47ce09dba188fc`.
- 172: accumulation differs in 2,105 bytes and final RGBA in 9 bytes; PF16 output exact.
- 174: post-blur differs in 10,373 bytes; PF16 output exact.
- 181: accumulation differs in 229 bytes and final RGBA in 1 byte; PF16 output exact.

Commands actually run:

- `F39-recheck.py INDEX` for all 17 small witnesses: successful original-AEX
  legacy capture, current Mac direct render and F32 public Smart render.
- `F39-full-frame.py`: Mac legacy assertions return 1 for the plane differences
  above; F32 public Smart succeeds and equals both final frames.
- `F39-package-evidence.py`: packages 14 A / 4 C rows; asserts every regenerated
  legacy output binds to a stored fixture or historical report.
- `F39-verify-finals.py`: **14/14 fresh F32 exact and 14/14 fresh Mac Smart exact**.
- F32 `session ... --watch function=0x4640,arg=rcx,size=16`: exit **2**, usage,
  no render. Full command and source-manifest check are in `F39-validation.json`.
- Source audit: F32 `main.rs` matches the registered build manifest. Its PNG
  path calls `into_rgba8()` before typed promotion. These inputs contain 191
  (small PF16), 198 (small PF32), or 1,795 (32x18 PF32) channel values not
  representable by that transport. No lossy PNG substitute was used.

Initial harness attempts exposed missing `ucrtmath` linkage and, for Zoom,
missing SDK include resolution. The recheck wrapper supplies the current math
archive and resolved SDK CPATH; reruns succeeded. These were harness fixes, not
numeric production changes. Execution used at most two emulator/build processes.
No fuzz campaign was needed to validate a production fix because no production
fix was made; corpus 35/35 and seed1 n300 were **not rerun** and are not newly claimed.

inference:

- The 14 measured final mismatches are oracle drift, not Mac final-output
  regressions: independently executed F32 original AEX equals current Mac.
- C assertions encode original AEX under the older emulation environment, not
  invented Mac traces. Keep them as historical oracle assertions. Exact final
  PF16/PF8 output does not prove internal FLOAT32 equality.
- A final-output match alone cannot authorize replacing intermediate expected
  planes. Neither a Mac capture nor an 8-bit-promoted F32 trace is valid evidence
  for these exact typed inputs. Therefore the original runner is not repointed
  and this ticket is blocked on raw typed F32 tracing. This is a capability and
  scope boundary, not a two-hypothesis stop or a permission rejection.

changed_files:

- `orchestra/reports/F39-recheck.py`: reproducible small witness comparisons.
- `orchestra/reports/F39-full-frame.py`: full-frame comparison retaining old assertions.
- `orchestra/reports/F39-package-evidence.py`: provenance/fixture packaging from AEX bytes.
- `orchestra/reports/F39-verify-finals.py`: fresh F32 and Mac Smart companion test.
- `orchestra/reports/F39-evidence.json`, `F39-validation.json`, and this report.
- `refs/fixtures/olmradialblur_F39_F32_final_20261023/`: 14 final-only fixture
  directories, each containing source, F32 output and provenance. Old artifacts
  remain present; provenance identifies the final expectations they supersede.

verify:

Run from this worktree, using MAIN's environment read-only:

```sh
PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3' -B orchestra/reports/F39-verify-finals.py > orchestra/state/F39-radial-fixture-oracle-recheck/verify.log 2>&1
```

Expected exit 0; last line: `14 final fixtures verified against fresh F32 and Mac Smart; stage assertions are not re-adjudicated.`

To reproduce the original comparisons, run the same interpreter with
`orchestra/reports/F39-recheck.py INDEX` for each small index in the table, then
`orchestra/reports/F39-full-frame.py` and `orchestra/reports/F39-package-evidence.py`.
Redirect each command to scratch logs and run sequentially. Expect the same
14 A / 4 C final classifications. Regenerable `*/ucrtmath` build directories may
be deleted afterwards; scripts rebuild them. `git diff --check` must pass.

next:

Provide an explicitly authorized F32-derived worker exposing raw typed input
plus passive stage watches (or equivalent exact-input trace transport), while
retaining F32 math/NaN behavior. Capture the required planes, expand from these
first-failing witnesses to every case in the affected multi-case commands, and
rebind the original tests to versioned F32 fixtures without deleting assertions.
The committed final fixtures and companion test are reviewable partial work;
they do not make the old 18 commands green.
