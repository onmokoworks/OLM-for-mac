#!/usr/bin/env python3
"""Evidence-backed original instability classifier; import classify() from here."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import time
import uuid

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'oracle'))
import olm_oracle as oracle


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def pixel_hash(a):
    return hashlib.sha256(a.tobytes()).hexdigest()


def variation(arrays):
    if not arrays:
        return None, {'successful': 0, 'distinct_outputs': 0, 'hashes': []}
    if any(a.shape != arrays[0].shape or a.dtype != arrays[0].dtype for a in arrays):
        raise ValueError('output dimensions/depth changed')
    mask = np.zeros(arrays[0].shape[:2], dtype=bool)
    for a in arrays[1:]:
        mask |= np.any(a != arrays[0], axis=2)
    hashes = [pixel_hash(a) for a in arrays]
    return mask, {'successful': len(arrays), 'distinct_outputs': len(set(hashes)),
                  'hashes': hashes, 'varying_pixels': int(mask.sum())}


def decide(reference, candidate, *, complete, mismatch, poison_proven=False,
           oob_observed=False):
    """Three-way triage, NOT a proof of absence of UB or an oracle pass.

    original_ub includes observed original nondeterminism. A stable render is
    finite evidence only. Exact comparisons use inconclusive/no_mismatch since
    the public verdict vocabulary intentionally has no 'exact' member.
    """
    if not complete:
        return 'inconclusive', 'incomplete_evidence'
    if reference['distinct_outputs'] > 1:
        return 'original_ub', 'original_nondeterminism'
    if poison_proven:
        return 'original_ub', 'undefined_memory_pattern_dependence'
    if oob_observed:
        return 'original_ub', 'observed_out_of_bounds_read'
    if candidate['distinct_outputs'] > 1:
        return 'inconclusive', 'candidate_nondeterminism'
    if mismatch:
        return 'stable_mismatch', 'stable_in_tested_trials'
    return 'inconclusive', 'no_mismatch'


def check_case(source):
    m = read_json(source/'case.json')
    for key in ('harness','reference','candidate'):
        if oracle.sha256(m[key]['path']) != m[key]['sha256']:
            raise ValueError(key + ' hash changed')
    for relative, digest in m['assets'].items():
        p = (source/relative).resolve(strict=True)
        if not p.is_relative_to(source) or oracle.sha256(p) != digest:
            raise ValueError('invalid/changed asset: ' + relative)
    for side in ('reference','candidate'):
        req = source/'requests'/f'{side}.json'
        if req.resolve() not in {(source/k).resolve() for k in m['assets']}:
            raise ValueError('request not bound by case assets')
        for a in read_json(req).get('assignments', []):
            if 'layer' in a:
                p = (source/a['layer']).resolve()
                if not p.is_relative_to(source) or p not in {(source/k).resolve() for k in m['assets']}:
                    raise ValueError('unbound/external layer asset')
    if 'input.png' not in m['assets']:
        raise ValueError('unbound input')
    if m['route'] not in oracle.ROUTES:
        raise ValueError('unknown route')
    return m


def auto_profile(m):
    for p in sorted((HERE/'profiles').glob('*.json')):
        profile = read_json(p)
        if (profile['module_sha256'] == m['reference']['sha256'] and
                m['route'] in profile['routes'] and profile.get('automatic',True)):
            return p
    return None


def save_mask(out, name, mask):
    if mask is None:
        return None
    Image.fromarray(mask.astype('uint8')*255, 'L').save(out/(name+'.png'))
    # All pixels, without a truncated coordinate list. NPZ also carries shape.
    np.savez_compressed(out/(name+'.npz'), mask=mask)
    return {'png': name+'.png', 'npz': name+'.npz', 'pixels': int(mask.sum())}


def classify(case, *, out=None, repeats=5, timeout=120, profile='auto',
             patterns=('00000000','3f3f3f3f'), poison_repeats=2, progress=None):
    """Run sequential owned workers. Returns a JSON-serializable verdict report.

    `profile=None` disables instrumentation. Default profiles bind the exact
    known binaries. No name/parameter/case-index blacklist is used.
    """
    if not 2 <= repeats <= 100 or not 2 <= poison_repeats <= 20:
        raise ValueError('repeats must be 2..100; poison_repeats 2..20')
    if not math.isfinite(timeout) or not 0 < timeout <= 600:
        raise ValueError('timeout must be in (0,600] seconds')
    patterns = [bytes.fromhex(p) for p in patterns]
    if len(set(patterns)) < 2 or len(patterns)>8 or any(not 1<=len(p)<=16 for p in patterns):
        raise ValueError('need 2..8 distinct nonempty patterns, at most 16 bytes each')
    source = Path(case).resolve(strict=True)
    m = check_case(source)
    out = Path(out).resolve() if out else HERE/'runs'/('classify-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
    profile_path = auto_profile(m) if profile == 'auto' else Path(profile) if profile else None
    contract = read_json(profile_path) if profile_path else None
    if contract:
        import probes
        probes.validate(contract,Path(m['reference']['path']),m['route'])
    out.mkdir(parents=True, exist_ok=False)
    for relative in m['assets']:
        dest = out/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source/relative,dest)
    oracle.write_json(out/'case.json',m)
    if contract:
        oracle.write_json(out/'profile.json',contract)
    depth, route_cmd = oracle.ROUTES[m['route']]
    records, arrays = [], {'reference':[], 'candidate':[]}
    complete = True

    def trial(name, side, debug=False, pattern=None):
        nonlocal complete
        if progress:
            progress(name)
        dest = out/name
        command = [m['harness']['path'],'--headless',route_cmd,m[side]['path'],
                   str(out/'input.png'),str(dest/'output.png'),str(out/'requests'/f'{side}.json')]
        if debug:
            process = probes.run(command,m[side]['path'],contract,dest,timeout,pattern)
        else:
            dest.mkdir()
            process = oracle.run_process(command,timeout,oracle.frame_deadline_environment(timeout))
            # run_process returns only after private-job close verified zero active children.
            process['cleanup_verified'] = True
            process['ok'] = process['returncode']==0 and not process['timeout'] and not process['cancelled']
            oracle.write_json(dest/'process.json',process)
        a = None
        if process['ok']:
            try:
                a = oracle.load_output(dest/'output.png',depth)
            except (OSError,ValueError) as e:
                process['artifact_error'] = repr(e)
                process['ok'] = False
        oracle.write_json(dest/'process.json',process)
        complete &= process['ok']
        r = {'trial':name,'ok':process['ok'],'cleanup_verified':process['cleanup_verified'],
             'pixel_sha256':pixel_hash(a) if a is not None else None,
             'process':'%s/process.json'%name}
        records.append(r)
        return a, process

    for i in range(repeats):
        for side in arrays:
            a,_ = trial(f'{side}-{i:03}',side)
            if a is not None:
                arrays[side].append(a)
    rmask, ref = variation(arrays['reference'])
    cmask, cand = variation(arrays['candidate'])
    mismatch = bool(arrays['reference'] and arrays['candidate'] and
                    not np.array_equal(arrays['reference'][0],arrays['candidate'][0]))
    mismatch_mask = None
    if arrays['reference'] and arrays['candidate'] and arrays['reference'][0].shape == arrays['candidate'][0].shape:
        mismatch_mask = np.any(arrays['reference'][0] != arrays['candidate'][0],axis=2)
    elif arrays['reference'] and arrays['candidate']:
        complete = False
    poison_mask, groups, oob, poison_proven = None, {}, [], False
    if contract:
        observer, proc = trial('observer','reference',True)
        oob = [e for e in proc['events'] if e.get('invalid')]
        # A read-only observer is retained separately; never mix debugger output
        # into the uninstrumented stability population.
        observer_control = (observer is not None and any(np.array_equal(observer,a) for a in arrays['reference']))
        mutated = []
        for i in range(poison_repeats):
            for pattern in patterns:  # interleave fixed predeclared patterns
                key = pattern.hex()
                a,pr = trial(f'poison-{key}-{i:02}','reference',True,pattern)
                groups.setdefault(key,[])
                if a is not None:
                    groups[key].append(a)
                mutated.extend(e for e in pr['events'] if e.get('mutated'))
        if all(len(g)==poison_repeats for g in groups.values()):
            stats = {k:variation(g)[1] for k,g in groups.items()}
            poison_mask,_ = variation([g[0] for g in groups.values()])
            # Prevent random variation from masquerading as pattern dependence.
            within_stable = all(v['distinct_outputs']==1 for v in stats.values())
            poison_proven = bool(within_stable and poison_mask.any() and mutated and
                                 contract.get('undefined_contract',False))
        else:
            stats = {k:variation(g)[1] for k,g in groups.items()}
    else:
        observer_control, stats = None, {}
    try:
        check_case(source)
        for relative, digest in m['assets'].items():
            if oracle.sha256(out/relative) != digest:
                raise ValueError('render asset changed')
    except (ValueError,OSError):
        complete = False
    verdict, reason = decide(ref,cand,complete=complete,mismatch=mismatch,
                            poison_proven=poison_proven,oob_observed=bool(oob))
    support = np.zeros_like(rmask) if rmask is not None else None
    if support is not None:
        support |= rmask
        if poison_proven:
            support |= poison_mask
    uncovered = int((mismatch_mask & ~support).sum()) if mismatch_mask is not None and support is not None else None
    report = {'schema_version':1,'verdict':verdict,'reason':reason,'complete':complete,
        'case':str(source),'case_sha256':oracle.sha256(source/'case.json'),'output':str(out),
        'identities':{k:m[k] for k in ('harness','reference','candidate')},'route':m['route'],
        'non_ae_debug_routes':m.get('non_ae_debug_routes',[]),'repeats':repeats,'timeout':timeout,
        'reference':ref,'candidate':cand,'baseline_mismatch':mismatch,
        'reference_variation':save_mask(out,'reference-variation',rmask),
        'candidate_variation':save_mask(out,'candidate-variation',cmask),
        'mismatch':save_mask(out,'mismatch',mismatch_mask),
        'poison':{'profile':str(profile_path) if profile_path else None,'groups':stats,
            'profile_sha256':oracle.sha256(out/'profile.json') if contract else None,
            'observer_hook_counts':proc['counts'] if contract else {},
            'unobserved_hooks':[h['name'] for h in contract['hooks'] if not proc['counts'].get(h['name'])] if contract else [],
            'pattern_dependence_proven':poison_proven,'observer_matches_uninstrumented':observer_control,
            'between_pattern_difference':save_mask(out,'poison-difference',poison_mask),
            'oob_reads':oob},
        'mismatch_pixels_outside_observed_ub_support':uncovered,
        'automatic_mismatch_exclusion':bool(verdict=='original_ub' and mismatch and
             uncovered==0 and cand['distinct_outputs']==1),
        'trials':records,'cleanup_verified':all(r['cleanup_verified'] for r in records),
        'limits':['AEXCompat CPU evidence; not native AE conformance',
            'Finite stability trials do not prove absence of undefined behavior',
            'original_ub does not excuse candidate differences outside observed pixel support',
            'No profile: host/stack/heap poisoning and instruction attribution are unavailable'],
        'source_sha256':{p.name:oracle.sha256(p) for p in
            [HERE/'ubdetect.py',HERE/'probes.py',HERE.parent/'record'/'win_debug.py',
             HERE.parent/'oracle'/'olm_oracle.py',HERE.parent/'witness'/'witness.py']}}
    oracle.write_json(out/'verdict.json',report)
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('classify')
    p.add_argument('--case',required=True,type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--repeats',type=int,default=5)
    p.add_argument('--timeout',type=float,default=120)
    p.add_argument('--profile',default='auto',help='JSON path, auto, or none')
    p.add_argument('--patterns',default='00000000,3f3f3f3f')
    p.add_argument('--poison-repeats',type=int,default=2)
    args=parser.parse_args(argv)
    try:
        r=classify(args.case,out=args.out,repeats=args.repeats,timeout=args.timeout,
                   profile=None if args.profile=='none' else args.profile,
                   patterns=args.patterns.split(','),poison_repeats=args.poison_repeats,
                   progress=lambda s:print(s,file=sys.stderr,flush=True))
        print(json.dumps({k:r[k] for k in ('verdict','reason','output','cleanup_verified')}))
        return 2 if r['verdict']=='inconclusive' else 0
    except KeyboardInterrupt:
        return 130
    except (ValueError,OSError) as e:
        print(json.dumps({'verdict':'inconclusive','reason':str(e)}))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
