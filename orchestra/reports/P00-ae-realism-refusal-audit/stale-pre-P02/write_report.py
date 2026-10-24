from pathlib import Path
import json,collections,sys,hashlib
ROOT=Path.cwd();state=ROOT/'orchestra/state/P00-ae-realism-refusal-audit'
sys.path.insert(0,str(ROOT/'tools/fuzz'));import ae_realism_audit as audit
rows=[json.loads(x) for x in (state/'matrix.jsonl').read_text().splitlines()]
base=[json.loads(x) for x in (state/'baseline.jsonl').read_text().splitlines()]
manifest=json.loads((state/'matrix-manifest.json').read_text())
meta={
 'generic-downsample':('G','Full-resolution-only downsample gate; source line 2040 onward selects generic versus exact owner.'),
 'generic-input-world':('G','Full input extent required; observed here only in the smaller-extent case.'),
 'smartrender-mapping':('G','ColorKeepIsOneToOne requires both downsample ratios 1/1 and matching origins (line 161).'),
 'prerender-inputs':('G','BoundedInDataGeometry requires literal 1/1 ratios (line 2536); callbacks are present.'),
 'public-admission':('G','Observed only with a smaller extent and neighborhood settings; IsPublicAdmission rejects non-full extents at line 2504.'),
 'prerender-partial-frame':('G','Request compared against full in_data dimensions, rejecting downsampled and ROI requests at line 2309 onward.'),
 'prerender-size-downsample':('G','Rejects unequal downsample numerator/denominator before checkout.'),
 'smart-predata-size':('G','Requires input and output dimensions equal full dimensions stored by PreRender; cropped input plus larger output fails.'),
 'pf32-smart-profile':('E','PF32 default fails the matrix/beta/oracle-profile admission disjunction (lines 2126–2149).'),
 'request-not-admitted':('G','Full-frame request/downsample restriction; GenericBetaRenderDimensions and request admission at lines 2640 and 2748.'),
 'prerender-frame-contract':('G','Smoother2 requires 1:1 downsample before requesting the full frame.'),
 'validate-world-shape':('G','Cropped input and PreRender-expanded output have different dimensions.'),
 'smartrender-partial-checkout':('G','Input/output must match the full polar-frame rectangle stored by PreRender.'),
 'world-extent-not-full-frame':('G','Smoother v1 explicitly requires full extents for its frame-wide walkers.'),
 'world-depth-32-unsupported':('I','Direct PF32 is outside v1 advertised capabilities: GlobalSetup out_flags2=0x08000000, without FLOAT_COLOR_AWARE (1<<12).'),
}
counts=collections.Counter(r['status'] for r in rows);bc=collections.Counter(r['status'] for r in base)
out=['status: blocked',
 'summary: Baseline and all available corpus-driven host-shape measurements completed without an oracle.',
 f'  Baseline: {len(base)} rows, {dict(bc)}; matrix: {len(rows)} rows, {dict(counts)}.',
 '  ColorKeep has no corpus JSON records; the requested ten retained-exact tuples cannot be supplied.',
 '  Other small corpora were sampled with replacement, explicitly recorded below. No plugin source changes.',
 '', 'facts:',
 '- Ground truth here is the fresh native arm64 Mach-O bundle returning from its public selector in the SDK-typed F51/F47d-derived host. This is not an AE session and not numerical conformance evidence.',
 f"- Source HEAD before audit files: `{manifest['source_head']}`. Host SHA-256: `{manifest['host_sha256']}`. Complete bundle/sample hashes and all per-row times/errors are in the adjacent evidence directory.",
 '- Build command: `python3 tools/fuzz/build_F47_bundles.py --scratch "$HOME/.cache/olm-emu/P00"` — all ten Universal Release bundles built successfully; `obj` and `pch` removed by builder.',
 '- Host command: `python3 tools/fuzz/ae_realism_audit.py --build-host` — native arm64 host built and registered as `P00` in `~/.cache/olm-emu/INDEX.json` with durable bundles/build.json.',
 '- Runtime: Apple M1 Pro, macOS 15.7.2 (24G325), arm64 host; shared 16 GB machine. Timing is host-selector wall time, not native AE frame-render benchmarking.',
 '- Baseline command: `python3 tools/fuzz/ae_realism_audit.py --phase baseline --jobs 1` — all ten defaults at 1920x1080 and 1/1, 1/2, 1/4, in 8/16/32bpc, before the matrix.',
 '- Matrix commands used `--phase matrix --jobs 1`, partitioned into `--plugins olmblur`, `--plugins colorkeep olmcolorkey olmdirectionalblur`, and `--plugins olmdistancegradation olmkirakira olmsmoother2 olmtoondilate radialblur olmsmoother`. Completed rows were preserved with `--resume` after host/driver preparation; binary identities were checked. At most two host processes ran at once, with separate scratch paths. The matrix partitions were concatenated without dropping any completed rows.',
 '- `memory_pressure` was checked before each plugin and every 100 rows; the driver stops below 30% free. Default performance was collected before parallel matrix work. No oracle, PNG comparison, numerical mismatch search, or disassembly inspection was performed; first numerical mismatch: not applicable.',
 '', 'The retained matrix is 19 situations × 3 depths × (default + 10 sampled records) for nine plugins, and 19 × 3 defaults for ColorKeep. Settings are one-factor-at-a-time, with an additional odd-half probe. `large-layer` is a 2560x1440 layer with a centered 1920x1080 request. `extent` zeroes pixels outside the centered hint. `roi` retains full checkout worlds. `cropped-expand` supplies a 960x540 origin-zero input with full 1920x1080 reference dimensions and honors PreRender output expansion. This last synthetic sparse-checkout case still needs native AE validation. See the host documentation for exact geometry and callback limits.',
 '', 'Retained sample provenance (saved `exact` means historical route evidence, not a new HEAD/large-frame exactness claim):',
 '', '| Plugin | Eligible records | Sampled records | Distinct parameter tuples sampled |', '|---|---:|---:|---:|']
for plugin,name in audit.PLUGINS.items():
 selected,n=audit.samples(plugin)
 unique=len({json.dumps(v['case']['parameters'],sort_keys=True) for p,v in selected})
 out.append(f'| {name} | {n} | {len(selected)} | {unique} |')
out += ['', 'Default 1920x1080 at 1/1, render-selector seconds (single invocation, not a benchmark distribution). Refusals are not successful frame timings; complete process times are also retained. **Over 2 seconds** is flagged where applicable.', '', '| Plugin | 8bpc | 16bpc | 32bpc |','|---|---:|---:|---:|']
for plugin,name in audit.PLUGINS.items():
 vals=[]
 for depth in (8,16,32):
  r=next(r for r in base if r['plugin']==plugin and r['situation']=='full' and r['depth']==depth)
  val=f"{r['result']['render_seconds']:.6f}" if r['status']=='ok' else 'refused (516)'
  if r['status']=='ok' and r['result']['render_seconds']>2:val='**'+val+' (>2s)**'
  vals.append(val)
 out.append('| '+name+' | '+' | '.join(vals)+' |')
out += ['', 'Matrix performance observations (successful selector times only; timeout is a >15-second **whole-process** observation and cannot give an exact selector duration):', '', '| Plugin | Successful rows >2s | Maximum selector seconds | Timeouts |', '|---|---:|---:|---:|']
for plugin,name in audit.PLUGINS.items():
 rr=[r for r in rows if r['plugin']==plugin]
 ok=[r['result']['render_seconds'] for r in rr if r['status']=='ok']
 out.append(f"| {name} | {sum(t>2 for t in ok)} | {max(ok,default=0):.6f} | {sum(r['status']=='timeout' for r in rr)} |")
out += ['', 'Smoother v1 uses Classic. Its direct PF32 probe is outside its declared float capability; this does **not** establish that a real AE 32bpc comp renders black, because AE can convert the effect input to a supported depth.', '', 'Per-plugin situation tables aggregate the three depths and selected records. Tag counts are exact event counts; `OK zero` is the number of successful outputs whose active bytes are all zero (not automatically wrong). `Other` separates timeouts, PF errors, crashes and unsupported host callbacks.']
for plugin,name in audit.PLUGINS.items():
 out += ['', '### '+name, '', '| Situation | OK | Refusal tags → count | Other | OK zero |','|---|---:|---|---|---:|']
 for situation,g in audit.situations():
  rr=[r for r in rows if r['plugin']==plugin and r['situation']==situation]
  tags=collections.Counter(t for r in rr for t in r['tags'])
  others=collections.Counter(r['status'] for r in rr if r['status'] not in ('ok','refusal'))
  out.append(f"| {situation} | {sum(r['status']=='ok' for r in rr)} | "+('; '.join(f'`{k}` × {v}' for k,v in tags.items()) or '—')+' | '+('; '.join(f'{k} × {v}' for k,v in others.items()) or '—')+f" | {sum(r['status']=='ok' and not r['result']['nonzero'] for r in rr)} |")
out += ['', 'inference:', '', 'Refusal classification: **G** = geometry/host shape; **E** = exactness/parameter admission; **I** = genuinely unsupported input under advertised capabilities. These categories describe the reached guard, not whether relaxing it is correct. Compound guards are interpreted using both their source and the observed situation.', '', '| Plugin / observed tag | Group | Source and reason | Original AEX plausibly fails? (inference only) |','|---|---|---|---|']
for plugin,name in audit.PLUGINS.items():
 tags=sorted({t for r in rows+base if r['plugin']==plugin for t in r['tags']})
 source=f'mac/{name}/{name}.cpp' if name not in ('OLMSmoother','OLMSmoother2') else f'mac/{name}/Mac/{name}_port.cpp'
 for tag in tags:
  namepart=tag.split(':',1)[1].split('@')[0];group,why=meta[namepart]
  line=tag.rsplit('@',1)[1]
  plausible={'G':'Not established. The host shapes are normal AE concepts; this port-specific full-frame guard is not evidence of an AEX restriction. Sparse/cropped checkout legality still needs a real host trace.', 'E':'Unknown. UI-valid parameters can plausibly be accepted by AEX; this retained-profile gate does not establish original failure.', 'I':'Plausible as a direct unsupported PF32 call. Original float capability was not independently checked; no claim about AE depth conversion.'}[group]
  out.append(f'| {audit.PLUGINS[plugin]} / `{tag}` | {group} | `{source}:{line}` — {why} | {plausible} |')
out += ['', 'No original-AEX execution or disassembly was consulted, so no AEX-failure statement above is a measured fact. The user-supplied real-AE Blur/ColorKey observations agree with the reproduced downsample guards. Successful host renders do not prove correct ROI, aspect, padding or downsample pixels.', '', 'changed_files:', '- `tools/emulation/aexcompat_patches/P00-host-realism.cpp`', '- `tools/emulation/aexcompat_patches/P00-host-realism.md`', '- `tools/fuzz/ae_realism_audit.py`', '- `orchestra/reports/P00-ae-realism-refusal-audit.md`', '- `orchestra/reports/P00-ae-realism-refusal-audit/` (compressed rows, manifests, summary and build provenance)', '', 'verify:', 'Run from this worktree. Redirect long commands into its scratch directory:', '', '```sh', 'mkdir -p orchestra/state/P00-ae-realism-refusal-audit', 'python3 tools/fuzz/build_F47_bundles.py --scratch "$HOME/.cache/olm-emu/P00" > orchestra/state/P00-ae-realism-refusal-audit/bundles.log 2>&1', 'python3 tools/fuzz/ae_realism_audit.py --build-host > orchestra/state/P00-ae-realism-refusal-audit/register.log 2>&1', 'python3 tools/fuzz/ae_realism_audit.py --phase baseline --jobs 1 > orchestra/state/P00-ae-realism-refusal-audit/baseline.log 2>&1', 'python3 tools/fuzz/ae_realism_audit.py --phase matrix --jobs 1 > orchestra/state/P00-ae-realism-refusal-audit/matrix.log 2>&1', 'python3 tools/fuzz/ae_realism_audit.py --summarize', 'git diff --check', '```', '', 'Expected: 90 unique baseline rows (38 OK / 52 refusals), 5700 unique matrix rows with all present corpus samples, and matching manifest/row counts. Times and timeout-versus-completion near 15 seconds depend on machine load; compare refusal tags by identity, not timing hashes. `--summarize` validates unique identities and expected row counts. Audit exit zero means the measurements completed, not that every render succeeded.', '', 'next:', '- **P01-host-shapes**: Blur, ColorKeep, ColorKey — trace real AE downsample, ROI and sparse world geometry; implement general coordinate/world handling only after independent AEX evidence. Preserve existing numerical lanes.', '- **P02-global-frame-host-shapes**: DirectionalBlur, KiraKira, RadialBlur, Smoother2 — separate full-frame algorithm requirements from preview/ROI request handling; validate full input retrieval, global coordinates and output expansion against actual AE/AEX.', '- **P03-distancegradation-admission**: independently cover the default PF32 profile and full-size work domain; repair downsample and sparse/full output negotiation with witnesses.', '- **P04-smoother-v1-capability**: verify original advertised depth and AE conversion behavior before considering a float implementation; trace legitimate extent behavior separately.', '- **P05-toondilate-host-conformance**: compare accepted downsample/ROI/aspect layouts numerically against original AEX; successful host return alone is not conformance.', '- **P06-corpus-real-size-coverage**: retain at least ten genuinely distinct exact tuples per plugin, particularly the absent ColorKeep corpus and effectively one-tuple DistanceGradation/ToonDilate selections. Re-run missing rows. This missing input is the blocking condition for the ticket as written.', '- **P07-real-size-performance**: investigate nondefault DirectionalBlur and RadialBlur timeout cases (including RadialBlur 1080p) using the retained parameter source paths; distinguish algorithmic work from host allocation/transport. Do not infer an AEX speed comparison.']
path=ROOT/'orchestra/reports/P00-ae-realism-refusal-audit.md';path.parent.mkdir(parents=True,exist_ok=True);path.write_text('\n'.join(out)+'\n')
print(path)
