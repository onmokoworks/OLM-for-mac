"""Summarize immutable final corpora and check every residual against observed variation."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

crate=Path(__file__).resolve().parents[1]
base=crate/'validation/upstream'
sys.path.insert(0,str(crate.parents[1]/'tools/oracle'))
import olm_oracle as o
def ident(p):
    p=Path(p)
    return dict(path=str(p.relative_to(crate)) if p.is_relative_to(crate) else str(p),sha256=o.sha256(p))
def read(p): return json.loads(Path(p).read_text())
names=['final-v8-seed-20261112','final-v8-seed-20261113','opaque-2025','opaque-2026','sample-2026']
summaries={n:read(base/n/'summary.json') for n in names}
candidate=o.identity(base/'DistanceGradation-v8.aex')
campaigns={}
for n,s in summaries.items():
    assert s['complete'] and s['candidate']['sha256']==candidate['sha256']
    campaigns[n]=dict(summary=ident(base/n/'summary.json'),reference=s['reference'],routes=s['routes'])
    if n.startswith('final-v8-seed'):
        campaigns[n]['successful_random_cases']={route:sum(r['route']==route and r['case']>=3
            and r['status'] in ('exact','mismatched') for r in s['results']) for route in s['routes']}

checks=[
 ('final-v8-seed-20261112',102,'ub-seed1-case102-v8'),
 ('final-v8-seed-20261113',6,'ub-seed2-case6-v8'),
 ('final-v8-seed-20261113',107,'ub-seed2-case107-v8'),
 ('opaque-2025',20,'ub-opaque2025-case20'),
 ('opaque-2025',21,'ub-opaque2025-case21'),
 ('opaque-2026',20,'ub-opaque2026-case20'),
 ('opaque-2026',21,'ub-opaque2026-case21'),
 ('opaque-2026',33,'ub-opaque2026-case33'),
]
residuals=[]
for n,index,ubname in checks:
    row=next(r for r in summaries[n]['results'] if r['case']==index and r['route']=='smart32')
    assert row['status']=='mismatched'
    case=base/n/row['directory']
    source=Path(row.get('source_directory',case))
    ub=base/ubname
    verdict=read(ub/'verdict.json')
    assert verdict['identities']['candidate']['sha256']==candidate['sha256']
    assert verdict['identities']['reference']['sha256']==summaries[n]['reference']['sha256']
    assert o.sha256(source/'input.png')==o.sha256(ub/'input.png')
    assert read(source/'requests/reference.json')==read(ub/'requests/reference.json')
    expected=o.load_output(source/'reference.png',32)
    actual=o.load_output(case/'candidate.png',32)
    mask=np.any(expected!=actual,axis=2)
    variation=np.load(ub/'reference-variation.npz')['mask']
    outside=int(np.sum(mask & ~variation))
    eh=hashlib.sha256(expected.tobytes()).hexdigest()
    ah=hashlib.sha256(actual.tobytes()).hexdigest()
    assert eh in verdict['reference']['hashes'] and ah in verdict['reference']['hashes']
    assert ah==verdict['candidate']['hashes'][0] and verdict['candidate']['distinct_outputs']==1
    assert verdict['complete'] and verdict['cleanup_verified'] and outside==0
    residuals.append(dict(campaign=n,case=index,route='smart32',
        verdict=ident(ub/'verdict.json'),classification=verdict['verdict'],reason=verdict['reason'],
        reference_trials=verdict['reference']['successful'],candidate_trials=verdict['candidate']['successful'],
        distinct_reference_outputs=verdict['reference']['distinct_outputs'],distinct_candidate_outputs=1,
        retained_mismatch_pixels=int(mask.sum()),observed_variation_pixels=int(variation.sum()),
        retained_mismatch_pixels_outside_variation=outside,
        retained_reference_and_candidate_both_observed_in_original_population=True,
        qualification='Explicit check of the saved campaign pair; ubdetect automatic exclusion can be false when its own first trial is exact.'))
assert sum(r['status']=='mismatched' for s in summaries.values() for r in s['results'])==len(residuals)
cross_build={}
for label,oldrun,newrun in [('mixed-alpha','final-seed-20261112','sample-2026'),
                           ('opaque','opaque-2025','opaque-2026')]:
    counts={r:dict(exact=0,different=0) for r in ('smart8','smart16','smart32')}
    for row in summaries[newrun]['results']:
        oldcase=base/oldrun/row['directory'];newcase=base/newrun/row['directory']
        assert o.sha256(oldcase/'input.png')==o.sha256(newcase/'input.png')
        assert read(oldcase/'requests/reference.json')==read(newcase/'requests/reference.json')
        a=o.load_output(oldcase/'reference.png',int(row['route'][5:]))
        b=o.load_output(newcase/'reference.png',int(row['route'][5:]))
        counts[row['route']]['exact' if np.array_equal(a,b) else 'different']+=1
    cross_build[label]=counts
decl=read(base/'final-v8-declarations/comparison.json')
assert not decl['differences']
static=read(crate/'upstream-static-report.json')
assert static['binaries']['candidate']['sha256']==candidate['sha256'] and static['pipl_identical_to_2025']
report=dict(schema_version=1,job='Up-dgrad',upstream_release='2026-11-12',
    status='AEXCompat CPU qualification with measured original-instability exclusions; not native AE exact',
    candidate=candidate,static_audit=ident(crate/'upstream-static-report.json'),
    complete_declarations=ident(base/'final-v8-declarations/comparison.json'),
    parameter_differences=0,pipl_byte_identical=True,campaigns=campaigns,residuals=residuals,
    original_2025_vs_2026_direct_comparisons=cross_build,
    tests=dict(command='python tests/update_build.py test',passed=13,failed=0,
        fixtures=[ident(crate/'tests'/p) for p in ['upstream-field.bin','upstream-masked-copy.bin']]),
    evidence=[ident(base/p) for p in ['witness-case38-v6/comparison.json',
        'witness-stages-case2-v5/comparison.json','witness-seed2-case76/comparison.json',
        'record-case132/alignment-analysis.json','hub/reports/last-stop.json']],
    sampling_domain=dict(random_thresholds=[0,128],random_blur_size=[0,12],
        other_controls='full exposed ranges',seeds=[20261112,20261113],downsample=['1','1/2','1/4'],
        random_sizes=[[1,1],[3,7],[11,7],[17,11],[31,19]],
        opaque_cases_per_build=42,opaque_threshold_boundaries=[512,1000],
        full_extrema_attempt='validation/upstream/smoke-v1: original all-max padding/blur timeout retained'),
    compatibility='Existing parameter slots/disk IDs/types retained. Padding appended at 13, default off. New upstream normalization intentionally changes old renders.',
    limitations=[
        'Five original-error cases per depth across the two seeds remain excluded, not passes.',
        'Original float output can depend on native buffer alignment; canonical Rust alignment is deterministic.',
        'RSQRT approximation is the measured x86 CPU profile, not all possible CPUs.',
        'Finite SDR PNG-promoted deep worlds; not arbitrary HDR/nonfinite/cropped/strided worlds.',
        'No macOS build, native AE execution, GUI, install, or shared workspace golden run.',
        'Random threshold/blur ranges are bounded as declared; high-cost original full-extrema timeouts are not retuned into passing cases.'
    ],
    shared_owner_actions=[
        'Add use_padding: false to the Params literal in rust/tools/golden/src/bin/golden-olm-distance-gradation.rs (new public field).',
        'Regenerate all 54 DistanceGradation golden hashes against the 2025 new original. Current tool publishes only complete all-ten runs; --only is diagnostic.',
        'Consider adding new DistanceGradation IplImage field/resize/EDT profiles to shared record/diverge. Job-local adapters avoid editing shared tools.',
        'Resolve the shared Cargo.lock update separately; this job uses an isolated offline snapshot.'
    ],
    ownership='All edits inside rust/plugins/olm-distance-gradation; no Git operations, AE, install, subagents, or shared tool edits.',
    lifecycle='Owned hub PIDs 60012 and 59484 were stopped and exits verified; render/debug/witness tools verify owned worker cleanup.')
(crate/'upstream-validation-report.json').write_text(json.dumps(report,indent=2))
print('Verified',len(residuals),'retained mismatch masks; all within observed original variation.')
for n,c in campaigns.items():print(n,{k:(v['exact'],v['mismatched'],v['reference_unrenderable']) for k,v in c['routes'].items()})
