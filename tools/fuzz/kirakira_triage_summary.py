#!/usr/bin/env python3
"""Select bounded-minimum T06 witnesses and summarize reproducible evidence."""
import argparse
import hashlib
from collections import Counter
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text())


def selected_cases(state):
    report = read(state/'gate-all.json')
    selected = []
    for signature, cluster in sorted(report['clusters'].items()):
        candidates = []
        for name in cluster['corpus']:
            if name and (ROOT/name).is_file():
                path = ROOT/name
                data = read(path)
                case = data['case']
                candidates.append((case['geometry'][0]*case['geometry'][1],
                    len(data.get('pixels_zlib_base64','')), data['index'], path, data))
        if not candidates:
            raise ValueError('No retained representative for '+signature)
        *_, path, data = min(candidates)
        selected.append((signature, cluster['count'], path, data))
    return selected


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', type=Path, default=ROOT/'orchestra/state/T06-triage-kirakira')
    p.add_argument('--select', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    if args.select:
        args.select.mkdir(parents=True, exist_ok=True)
        for _, _, path, _ in selected_cases(args.state):
            shutil.copyfile(path,args.select/path.name)
        print('selected',len(selected_cases(args.state)))
    if not args.output:
        return
    census = read(args.state/'census.json')
    baseline = read(ROOT/'reports/fuzz/olmkirakira_20261021.json')
    prior = {c['index']:c for c in baseline['cases']}
    groups = {}
    for case in census['cases']:
        for route, guards in case['refusal_guards'].items():
            assert len(guards) == 1
            guard = guards[0].split('@')[0]
            group = groups.setdefault(guard,[])
            group.append((case,route))
    declarations = {d['slot']:d for d in read(ROOT/'tools/fuzz/declarations/olmkirakira.json')['parameters']}
    violations = []
    for case in census['cases']:
        for parameter in case['parameters']:
            kind, value = parameter['kind'], parameter['value']
            declaration = declarations[parameter['slot']]
            valid = (all(0 <= v <= 255 and int(v) == v for v in value) if kind == 'c'
                     else -32768 <= value < 32768 if kind == 'a'
                     else declaration['valid_min'] <= value <= declaration['valid_max'])
            if not valid:
                violations.append([case['index'],parameter['slot']])
    ranked = []
    for guard, rows in groups.items():
        ranked.append(dict(guard=guard,count=len(rows),
            routes=dict(Counter(route for c,route in rows)),
            aex_ok=sum(c['result']['oracle']['status']=='ok' for c,route in rows),
            depth=dict(Counter(c['depth'] for c,route in rows)),
            indices_by_route={route:[c['index'] for c,r in rows if r==route] for route in ('classic','smart')}))
    ranked.sort(key=lambda r:-r['count'])
    experiments = {}
    for name in ('tuples','request','layout','all','sanitizers'):
        path = args.state/f'gate-{name}.json'
        if not path.exists():
            continue
        data = read(path)
        experiments[name] = {k:data[k] for k in ('status','summary','provenance','completed','seed','jobs','max_size','shrink_attempts','shrink_seconds','cluster_count','framework_sha256')}
        experiments[name]['cases'] = [{k:v for k,v in c.items() if k not in ('parameters','elapsed_seconds')} for c in data['cases']]
        if name == 'all':
            retained = ROOT/'tests/fuzz_corpus/olmkirakira_gate_off_T06'
            for row in experiments[name]['cases']:
                if row.get('corpus'):
                    filename = Path(row['corpus']).name
                    for candidate in (retained/filename, retained/'other_reductions'/filename):
                        if candidate.is_file() and candidate.read_bytes() == (ROOT/row['corpus']).read_bytes():
                            row['corpus'] = str(candidate.relative_to(ROOT))
                            break
        errors = {}
        for route in ('classic','smart'):
            outcomes = [c['result']['routes'][route] for c in data['cases'] if 'result' in c]
            errors[route] = dict(
                negative_returncode=sum(r.get('returncode',0)<0 for r in outcomes),
                sanitizer_diagnostic=sum('runtime error:' in r.get('diagnostic','') or 'Sanitizer' in r.get('diagnostic','') for r in outcomes),
                refusal_errors=dict(Counter(r['error'] for r in outcomes if r['status']=='refusal')))
        experiments[name]['error_breakdown'] = errors
    details = read(args.state/'cluster-details.json') if (args.state/'cluster-details.json').exists() else []
    clusters = []
    for signature,count,path,data in selected_cases(args.state):
        case = data['case']
        clusters.append(dict(signature=signature,count=count,index=data['index'],
            geometry=case['geometry'],depth=case['depth'],
            input_sha256=data['input_sha256'],corpus=path.name,
            classification='unexplained',
            classification_basis='Output disagreement established; no paired AEX/Mac intermediate values for this input. Signature is not a proven cause.',
            details=[d for d in details if d['index']==data['index'] and d['input_sha256']==data['input_sha256']]))
    result = dict(schema='olm-kirakira-triage/1',baseline='reports/fuzz/olmkirakira_20261021.json',
        additional_dependencies_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'core').glob('kirakira_*.h'))},
        census={k:census[k] for k in ('summary','provenance','completed','seed','jobs','framework_sha256')},
        parameter_bound_violations=violations,
        replay_checks={name:{k:read(args.state/name)[k] for k in ('completed','replay_matches_saved','status')} for name in ('replay.json','cluster-replay.json') if (args.state/name).exists()},
        unchanged_baseline_results=sum(c['result']==prior[c['index']]['result'] for c in census['cases']),
        ranked_guards=ranked,experiments=experiments,clusters=clusters)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('wrote',args.output,'clusters',len(clusters))


if __name__ == '__main__':
    main()
