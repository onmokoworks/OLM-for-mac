# Module split and staged validation plan

1. `types.rs`, `frame.rs`, `lut.rs`: RGBA scratch types, PF8/PF16 loading and packing,
   key filtering, sRGB transfers and the captured 10,000-entry LUTs. Compare each
   kernel with the unchanged C++ frame-setup include before proceeding.
2. `scan.rs`: classifier and eight axial/six diagonal scanners; test every
   location of deterministic class planes, including boundaries and padded rows.
3. `gamma.rs`: palette membership, gamma/premultiply, scalar composite and
   post-unpremultiply; compare raw float words with C++ across polygon sizes.
4. `polygon.rs`, `weights.rs`, `geometry.rs`, `geometry_generated.rs`:
   bounded 12-vertex storage, corner samples, coverage weights, all cardinal
   families and the 222-case switch. Verify each family before full-frame tests.
5. `algorithm.rs`: class-plane construction and full staged render, checked
   allocations, deterministic row parallelism and C++ full-frame comparisons.
6. `ae.rs` and PiPL in `build.rs`: only after the pure pipeline passes; preserve
   original parameter slots/disk IDs, dynamic controls, SmartFX ownership and
   admission/refusal rules. Follow the pilots' binary PiPL embedding and aliases.
7. Original-AEX inventory and Smart8/16/32 oracle campaigns: at least 200 random
   cases per depth across two seeds, downsample 1, 1/2, 1/4, `--jobs 3` and equal
   host deadlines on both sides. Record failures separately from exact renders.

## Status

The pure render pipeline and AE adapter are implemented. **20 release tests pass,
zero failures.** All 222 polygon dispatch labels are translated mechanically.
Original-AEX inventory is identical; the complete 294-byte Windows PiPL is identical.
The final original-AEX campaign passed **618/618 comparisons**: **206 per depth**,
including **200 randomized cases per depth across two seeds**, with zero pixel
mismatches, reference failures, candidate failures or timeouts. Downsample 1,
1/2 and 1/4 are all covered. No requested port stage remains unfinished.

| Seed | Smart8 exact | Smart16 exact | Smart32 exact | Random cases per depth |
| --- | ---: | ---: | ---: | ---: |
| 20261116 | 103 | 103 | 103 | 100 |
| 20261117 | 103 | 103 | 103 | 100 |
| Total | **206** | **206** | **206** | **200** |

Each depth has 70 exact cases at downsample 1, 68 at 1/2 and 68 at 1/4.
Of those, 68/66/66 are randomized; six are default/min/max checks across the
seeds. `campaign-summary.json` binds the totals and per-seed details to the
frozen binary. `inventory-verified/summary.json` confirms the delivered
candidate's inventory; `pipl-comparison.json` confirms all 294 resource bytes.
Earlier smoke/regression renders are additional evidence and excluded from
these final campaign counts.

The delivered test candidate is `OLMSmoother2-verified.aex`. Earlier DLL copies
and interrupted campaign directories are diagnostic history, not final evidence.

## Measured C++ comparisons

The reference TU includes the actual unchanged C++ files. For gamma and class
plane code, `build.rs` extracts unchanged bodies using explicit source markers;
it fails if those markers disappear. A wrapper supplies arguments and returns
results; expected algorithms are not separately reimplemented in the tests.
Production Rust code has no calls to `sm2_ref_*`. As in the pilot, Cargo builds
the reference archive, but only `#[cfg(test)]` code references its functions.
C++ uses clang-cl, C++17, contraction off, fast math off, release optimization.
Both sides use the same already-qualified `olm-math` UCRT implementation: these
are translation tests, not new independent qualification of UCRT.

| Stage | Actual comparison coverage | Result |
| --- | --- | --- |
| PF8/PF16 load and pack | All 256/65,536 integer codes, each loaded and packed; additionally 20,000 random raw-float PF16 packs and finite random PF8 packs | Raw exact |
| Transfers | 50,008 inputs each for literal decode, decode LUT, encode LUT: every one of 10,000 knots and adjacent words, special endpoints, 20,000 random normalized floats | 150,024 raw exact calls |
| Frame leaves | 512 × 37 pixels × four operations (unpremultiply, palette, scalar key, runtime decode); empty/full palettes, hits, threshold boundary, hidden RGB, NaN channel | 75,776 pixel comparisons exact |
| Classifier and attenuation | All 32 boolean classifier combinations; 20,000 trapezoid cases | Exact |
| 14 scanners | Seeds `0x5162`, `0x20261112`, each 486,528 outputs; 48 plane patterns, sizes 1×1, 1×7, 7×1, 3×7, 11×9, 31×19; every coordinate; row padding 0–4 bytes | 973,056 exact outputs |
| Gamma stages | Polygon counts 0–12, 512 cases/count, four stage calls/case; gamma 0/0.1/0.5/1/2.2/5/10, negative/zero/one alpha, weights outside [0,1] | 26,624 exact stage calls |
| Gamma palette membership | Versions 1/2, modes None/Colors/All, palette counts 0–5, center/sample hits and misses | 4,608 exact cases |
| Exceptional scalar arithmetic | Signed zero, infinity, signed/payload NaNs and sNaN pairs; gamma disabled; premultiply/composite/post-unpremultiply | 192 exact stage calls |
| Curves and literal encode | 20,000 inputs, eight curve indices; 20,000 binary64 literal encode calls | 180,000 exact calls |
| Coverage weights | All 16 endpoint keys, spans 4–256, offsets −2 through span+2, both C++ scalar-rounding flags | 1,092,960 exact pair calls |
| Coverage lines | 20,000 random segments, both C++ flags | 40,000 exact line calls |
| Corners and normalization | Five sizes, every coordinate, all 16 corner masks, normalization on/off, pixel-strided padding | 4,320 exact polygons |
| Class plane | Six sizes, 48 patterns, six Smooth Range values (0/1/2/3/50/100), including transparent and nonfinite pixels | 1,728 frames exact at each of 1/3/7 threads |

| Directional leaves | Two seeds, 512 descriptor/class patterns per seed, all 32 leaves | 32,768 exact results/counts/vertices/weights |
| Complete polygons | Two seeds, four dimensions, 256 patterns, five positions; all 256 switch indices forced at interior pixels | 10,240 exact polygons |
| Full float render | Two seeds, four sizes, 144 parameter/pixel patterns each; setup through final RGB transfer/premultiply | 1,152 frames exact at each of 1/3/7 threads (3,456 comparisons) |
| Source identity SHA-256 | Actual C++ core header; lengths 0?256, 1024, 8192, 65536 | 260 exact digests |

## Reproduction and identity

From the repository root:

```powershell
python rust/plugins/olm-smoother2/generate_geometry.py --stage all
python rust/plugins/olm-smoother2/validate.py
python rust/plugins/olm-smoother2/run_campaign.py
python rust/plugins/olm-smoother2/summarize_campaign.py
```

`validate.py` sets `CARGO_TARGET_DIR=D:\olm-rs-target\P-smoother2` and runs only
`cargo build/test --release -p olm-smoother2 -j 2 --offline`. It binds source,
reference, LUT, binary, harness and worker hashes in `validation-report.json`.
`run_campaign.py` runs seeds sequentially, each with `--jobs 3`, `--cases 103`,
`--routes smart8,smart16,smart32`, `--downsample 1,1/2,1/4`, `--timeout 120`.
Both sides receive `AEXCOMPAT_FRAME_DEADLINE_MS=120000`. Output directories must
be new; archive names in the runner must be changed before intentionally rerunning.

| Artifact | SHA-256 |
| --- | --- |
| Original OLMSmoother2.aex | `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7` |
| Delivered candidate | `a5196bd1bfab23fbfc82c30c6eaf168b64d9fc9139ea513d37bbe80bae551609` |
| Built DLL | `c901503de5f3e360745970d7a30bcf1bb530e66fea7513c5a05ef43005f12771` |
| Harness | `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27` |
| Worker | `0481df5fa425af28f0e8a39ea9386185de13656c3c9d488042bed2244bdf8302` |

The later test-only addition produces a new linker timestamp/PDB GUID. The frozen
campaign AEX and rebuilt DLL are byte-identical after excluding only PE/debug
timestamps and the 16-byte PDB GUID (`rebuild-equivalence.json`); all executable,
data, unwind, relocation and resource sections match. The full candidate SHA
above is the identity used for final oracle counts.

## Translation and adapter details

- `generate_geometry.py` is retained in the crate. It recognizes only the C++
  subset present here, rejects unknown statements, preserves expression order,
  all 222 labels and explicit switch fallthroughs, and omits diagnostic-only
  trace/histogram branches. `geometry-generation.json` binds each translated
  function to its C++ source hash. Normal diagnostic selector values remain zero.
- `geometry.rs` bridges the generated code to verified scanners, coverage weights
  and checked 12-vertex storage. Synthetic arbitrary class bytes at boundaries
  can send the unchanged C++ append outside its allocation. Boundary comparisons
  therefore use real class planes; interior tests explicitly force all 256 indices.
  Rust rejects out-of-bounds appends rather than reproducing undefined memory reads.
- `algorithm.rs` preserves setup, class generation, polygon, adaptive gamma,
  premultiply, separate scalar composite, post-unpremultiply and final LUT order.
  Count-zero polygons bypass gamma/compositing. All depths use captured runtime
  decode/encode LUTs and separate scalar composite, exactly as current C++ does.
  PF8/PF16 loads and packs are separately compared; PF32 writes raw words.
- `ae.rs`, `ae_setup.rs`, `ae_boundary.rs` and `dynamic.rs` retain original slots,
  disk IDs, defaults (including white key), flags, dynamic controls, SmartFX RGB
  preservation and the `entry_point` alias. The shared pilot boundary is copied
  locally only where this plug-in needs additional behavior: active-color-only
  suite fetches, source-bound admission, release error propagation, and publishing
  staged output after successful checkin. No shared source was changed.
- Public classic rendering is refused. Generic Smart admission preserves the
  C++ 1?8192 dimensions, ranges, versions, finite gamma, matching depth/origin,
  nonoverlap and signed row-span limits. `admission.rs` retains the stronger
  source/parameter fixture union and its world flags/origin/downsample contract.
  `sha256.rs` translates `core/olm_sha256_rows.h` for that source identity check.
- Windows PiPL follows the pilots' binary-resource embedding, including the
  two-byte eINF declaration. macOS entry/resource declarations are present but
  have not been built here.

## Investigation history

The first adapter smoke campaign (`oracle-smoke`) passed 36/36 renders. The
transactional-output revision then failed before rendering because it asked the
host for the format of a copied temporary world. The host recognizes its own
world pointers. Format validation now runs on the original checked-out worlds
before staging. `oracle-adapter-fix` confirms the corrected path at every depth
and downsample. A focused mock-host regression also verifies original-world format queries,
immutable input, one checkin, balanced suite releases and unchanged output on
a late checkin failure. No numerical constants were tuned; no pixel mismatch was fixed
by approximation.

Three interrupted campaigns are excluded from final counts:
`oracle-seed20261116`, `oracle-final-seed20261116`, and
`oracle-final-v2-seed20261116`. A shell interrupt did not stop their Python
children. Exact task-owned parent PIDs and descendants were identified, stopped,
and verified absent; `cancelled-processes.json` records ownership. Both final runs exited 0 and were awaited normally. The oracle itself uses per-invocation Windows Jobs,
waits for child exit, terminates remaining descendants and verifies zero active
processes before closing the job.

## Remaining limits and validation outside this job

- No native AE, macOS build or GPU validation is claimed. No GUI was opened
  and AE was never launched or touched. The requested Windows CPU port,
  staged reference tests, inventory/PiPL and two-seed oracle campaign are complete.
- AEXCompat reports `source_newer_than_worker`; evidence is tied to the supplied
  binary worker hash, not unbuilt host source. This is host-emulator evidence.
- The C++ polygon/cardinal reconstruction remains public-beta scope; matching
  this corpus does not prove every image, scan length or parameter combination.
  The source-bound retained fixtures are preserved in code, but their large
  native-host fixture corpus was not rerun in this job.
- Full-render tests exercise public modes only. The unreachable internal
  luma-adaptive mode is not exposed; its six curve leaves remain tested.
- PF8 NaN-to-integer packing has no portable C++ contract. Nonfinite scalar
  kernel tests do not establish arbitrary nonfinite full-frame behavior.
- Coverage weight comparisons cover spans 4?256 and the listed random segments;
  this is not an exhaustive geometry proof. Invalid nonfinite integer casts
  are refused by the Rust coverage primitives.
- Potential shared-crate candidates: source-identity SHA-256, nonblack color
  defaults and transactional SmartFX output. No new third-party package beyond
  the existing pilots' `olm-ae`, `pipl`, `winres` and `cc` dependencies was added.

## Scope

Only `rust/plugins/olm-smoother2/**` is owned/edited. Build artifacts use the
assigned target directory. No commits, installs, subagents or GUI actions were
performed. C++ reference functions are used by tests, never by the Rust render
path. UCRT combined artifacts remain OLM-internal and must not be published
standalone.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.

The `campaign-*`, `inventory-*`, `original-inventory-run`, `oracle-*` and
`standalone/` directories are also **local-only evidence/build workspaces**.
Root-level campaign-summary, geometry-generation, rebuild-equivalence,
rebuild-sections, process records and validation-report JSON are retained.
