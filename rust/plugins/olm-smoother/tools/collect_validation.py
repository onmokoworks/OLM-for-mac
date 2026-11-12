"""Summarize retained oracle runs without changing their evidence."""
from pathlib import Path
import collections, hashlib, json, sys

CRATE = Path(__file__).resolve().parents[1]
ROOT = CRATE.parents[2]

def identity(path):
    p=Path(path)
    return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    runs=[];pids=set()
    for name in sys.argv[1:]:
        path=CRATE/'validation'/name/'summary.json'
        s=json.loads(path.read_text(encoding='utf-8'))
        counts=collections.defaultdict(collections.Counter)
        random=collections.defaultdict(collections.Counter)
        for r in s['results']:
            counts[r['route']][r['status']]+=1
            if r['case']>=3:random[r['route']][r['status']]+=1
            for proc in r.get('processes',{}).values():
                if proc.get('pid'):pids.add(proc['pid'])
        runs.append({'name':name,'summary':identity(path),'seed':s['seed'],
            'cases':s['cases'],'jobs':s['jobs'],'timeout_seconds':s['timeout_seconds'],
            'environment':s['render_environment_overrides'],
            'reference':s['reference'],'candidate':s['candidate'],'harness':s['harness'],
            'oracle':s['tool'],'sizes':s['sizes'],'downsample':s['downsample'],
            'inventory_diff':s['inventory_diff'],
            'counts':dict(counts),'random_counts':dict(random),
            'non_exact':[{k:r.get(k) for k in ('case','route','status','processes','comparison')} for r in s['results'] if r['status']!='exact']})
    source={}
    for p in sorted((ROOT/'mac/OLMSmoother/Mac').glob('*.inc')):
        source[str(p.relative_to(ROOT))]=identity(p)['sha256']
    for p in sorted((CRATE/'src').glob('*.rs')):
        source[str(p.relative_to(ROOT))]=identity(p)['sha256']
    for rel in ['build.rs','Cargo.toml','tests/reference.cpp','tools/translate.py']:
        p=CRATE/rel;source[str(p.relative_to(ROOT))]=identity(p)['sha256']
    report={'schema_version':1,'plugin':'OLMSmoother v1','runs':runs,
        'source_sha256':source,'owned_harness_pids':sorted(pids),
        'limitations':['AEXCompat CPU harness, not native AE','macOS not built or run',
            'PNG inputs promoted to 16-bit; no exhaustive native 16-bit input space',
            'No SmartFX or 32 bpc (undeclared by original)',
            'Oracle does not exercise padded/origin-shifted native host worlds; local C++ and Rust tests cover padding and cropped extents']}
    (CRATE/'validation-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{'run':r['name'],'counts':r['counts']} for r in runs],indent=2))

if __name__=='__main__':main()
