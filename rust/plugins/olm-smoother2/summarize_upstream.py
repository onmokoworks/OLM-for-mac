"""Bind completed upstream evidence to the delivered candidate and source files."""
import hashlib,json
from collections import Counter
from pathlib import Path
from verify_upstream_leaves import HERE,ROOT,WORK,ORIGINAL,save

def identity(path):
    path=Path(path)
    return dict(path=str(path.resolve()),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def main():
    candidate=identity(WORK/'OLMSmoother2-final.aex')
    assert candidate['sha256']==identity('D:/olm-rs-target/Up-smoother2/release/olm_smoother2.dll')['sha256']
    runs=[];totals={2025:Counter(),2026:Counter()}
    for year,seed in [(2025,20261114),(2025,20261115),(2025,20261116),(2026,20261116)]:
        directory=WORK/f'final-{year}-{seed}'
        j=json.loads((directory/'summary.json').read_text())
        assert j['exit_code']==0 and j['candidate']['sha256']==candidate['sha256']
        versions=Counter();fractional=0
        cases=json.loads((directory/'cases.json').read_text())
        for case in cases[3:]:
            values={v['slot']:v['value'] for v in case['assignments'] if 'value' in v}
            versions[values.get(7,2)]+=1
            value=values.get(6,2);fractional+=int(value!=int(value))
        runs.append(dict(year=year,seed=seed,summary=identity(directory/'summary.json'),resident='resident_tool' in j,
                         routes=j['routes'],random_cases_per_depth=len(cases)-3,random_versions=dict(versions),fractional_ranges=fractional))
        for route,row in j['routes'].items():
            assert row['exact']==len(cases)
            totals[year][route]+=row['exact']
    focused=json.loads((WORK/'oklab-gamma/summary.json').read_text())
    assert focused['counts']=={'exact':27} and focused['identities']['candidate']['sha256']==candidate['sha256']
    for route in totals[2025]:totals[2025][route]+=9
    declarations=json.loads((WORK/'declarations-final-comparison.json').read_text())
    assert declarations['raw_identical'] and declarations['pipl_identical']
    cleanup=json.loads((WORK/'hub/reports/last-stop.json').read_text());assert cleanup['exited'] and not cleanup['remaining']
    golden_path=ROOT/'rust/tools/golden/golden.json'
    golden_ids=sorted(k for k in json.loads(golden_path.read_text()) if k.startswith('OLMSmoother2-'))
    assert len(golden_ids)==54
    report=dict(date='2026-11-13',candidate=candidate,
        originals=dict(ae2025=identity(ORIGINAL),ae2026=identity(ORIGINAL.parent.parent/'2026/OLMSmoother2.aex'),old=identity(ROOT.parent/'ghidra_windows_aex/OLMSmoother2.aex')),
        ucrt=dict(**identity('C:/Windows/System32/ucrtbase.dll'),version='10.0.26100.9711',symbol='cbrtf',rva='0x54ed0',import_library='api-ms-win-crt-math-l1-1-0.dll'),
        final_totals={str(k):dict(v) for k,v in totals.items()},campaigns=runs,
        primary_campaign_random_cases_per_depth=200,primary_campaign_downsample_counts={'1':70,'1/2':68,'1/4':68},
        primary_campaign_random_versions={'1':73,'2':68,'3':59},
        tests=dict(release_tests=21,cbrtf_raw_words=1033289,matrices=256,class_pixels=735,recorded_calls=20,recorded_replays=40),
        declarations=declarations,old_domain=json.loads((WORK/'old-domain/summary.json').read_text())['counts'],
        old_domain_stability=identity(WORK/'old-domain-stability/verdict.json'),
        minimized_boundary=identity(WORK/'old-new-class-minimized-v2/reduction.json'),
        lookup_counts={'exact':516,'fuzzy':19,'unknown':39},hub_cleanup=cleanup,
        final_cleanup=identity(WORK/'final-cleanup.json'),
        golden_rebaseline=dict(manifest=identity(golden_path),case_ids=golden_ids,updated=False,reason='No per-plugin publishing support; shared files outside ownership'),
        sources=[identity(f) for f in sorted((HERE/'src').glob('*.rs'))]+[identity(HERE/f) for f in ['build.rs','pipl_build.rs','Cargo.toml','examples/upstream_witness.rs']],
        needed_shared_changes=['Hoist the qualified OLM-internal cbrtf wrapper into olm-math.',
            'Golden tool supports diagnostic subsets only: owner must regenerate 54 Smoother2 hashes and add Oklab/fractional cases.',
            'Hub needs an explicit per-instance data/project directory option; local launcher currently overrides defaults.',
            'Diverge reducer should separate input dtype from output dtype; local adaptation permits u8 output with f32 input.',
            'Record replay dispatcher needs Smoother2 adapters; local replay bridge verifies all 20 calls.'],
        limitations=['AEXCompat CPU only; no native AE, macOS, GPU, project/keyframe migration or UI interaction qualification.',
            'Cube-root raw-word campaign is sampled, not exhaustive; errno, FP exception flags and alternate rounding modes excluded.',
            'Full-frame sources are SDR PNG-promoted; signed/HDR matrix leaves do not establish arbitrary HDR frame coverage.',
            'Historical 2.1.0 validation/goldens are not the authority for this update.'])
    save(HERE/'upstream-validation.json',report)
    print(json.dumps(dict(totals=report['final_totals'],candidate=candidate['sha256']),indent=2))

if __name__=='__main__':main()
