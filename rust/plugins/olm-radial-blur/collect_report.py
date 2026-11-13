"""Collect bounded, identity-checked results without changing oracle verdicts."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import pefile

OWN=Path(__file__).resolve().parent
def identity(path):
    path=Path(path).resolve()
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--campaign',type=Path,action='append',required=True);ap.add_argument('--triage',type=Path,action='append',default=[]);ap.add_argument('--candidate',type=Path,required=True)
    args=ap.parse_args();candidate=identity(args.candidate)
    adjudications={}
    for path in args.triage:
        summary=json.loads((path/'summary.json').read_text());assert summary['complete']
        for row in summary['results']:
            assert row['replay_candidate']['sha256']==candidate['sha256']
            adjudications[str(Path(row['source']).resolve())]=row
    campaigns=[];totals={r:{'random_exact':0,'extrema_exact':0,'reference_nondeterministic':0,'unresolved':0,'seeds':[]} for r in ['smart8','smart16','smart32']}
    for path in args.campaign:
        s=json.loads((path/'summary.json').read_text());assert s['complete'];assert not s['inventory_diff'];assert s['candidate']['sha256']==candidate['sha256']
        plans=json.loads((path/'cases.json').read_text())
        assert all(next(a['value'] for a in c['assignments'] if a['slot']==25)!=3 for c in plans)
        counts={r:{'random_exact':0,'extrema_exact':0,'reference_nondeterministic':0,'unresolved':0,'excluded':[]} for r in totals}
        for row in s['results']:
            c=counts[row['route']];source=path/row['directory'];verdict=row['status']
            if verdict=='exact': c['random_exact' if row['case']>=3 else 'extrema_exact']+=1
            else:
                triage=adjudications.get(str(source.resolve()))
                control = (triage or {}).get('offset_control_evidence', {})
                offset_qualified = all(control.get(k) is True for k in [
                    'same_input_params_route_except_slot28', 'zero_offset_exact',
                    'positive_offset_exact', 'cpp_zero_read_equivalent',
                    'mismatches_within_underread_support'])
                if (triage and triage['classification']=='reference_nondeterministic'
                    and triage['candidate_unique']==1 and triage['all_replays_succeeded']
                    and (triage['has_exact_replay'] or offset_qualified)):
                    c['reference_nondeterministic']+=1
                    c['excluded'].append({'case':row['case'],'reason':'Reference output changes for identical saved input/request','triage':triage})
                else:
                    c['unresolved']+=1;c['excluded'].append({'case':row['case'],'status':verdict,'triage':triage})
        for route,c in counts.items():
            for key in ['random_exact','extrema_exact','reference_nondeterministic','unresolved']:totals[route][key]+=c[key]
            if c['random_exact']:totals[route]['seeds'].append(s['seed'])
        coverage={'downsample':dict(Counter(c['downsample'] for c in plans)),
                  'blur_type':dict(Counter(str(next(a['value'] for a in c['assignments'] if a['slot']==1)) for c in plans)),
                  'noise_type':dict(Counter(str(next(a['value'] for a in c['assignments'] if a['slot']==25)) for c in plans)),
                  'size':dict(Counter('x'.join(map(str,c['size'])) for c in plans))}
        campaigns.append({'directory':str(path.resolve()),'summary':identity(path/'summary.json'),'seed':s['seed'],'sizes':s['sizes'],'downsample':s['downsample'],'jobs':s['jobs'],'timeout_seconds':s['timeout_seconds'],'reference':s['reference'],'candidate':s['candidate'],'harness':s['harness'],'counts':counts,'raw_routes':s['routes'],'coverage':coverage,'type3_exclusions':len(json.loads((path/'exclusions.json').read_text())['excluded'])})
    original=Path(campaigns[0]['reference']['path']);pipl=[]
    for path in [original,args.candidate]:
        pe=pefile.PE(str(path));e=next(e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if str(e.name).upper()=='PIPL');d=e.directory.entries[0].directory.entries[0].data.struct;b=pe.get_data(d.OffsetToData,d.Size)
        pipl.append({**identity(path),'length':len(b),'pipl_sha256':hashlib.sha256(b).hexdigest(),'bytes':b.hex()})
    pipldiff={'equal':pipl[0]['bytes']==pipl[1]['bytes'],'records':pipl};assert pipldiff['equal']
    (OWN/'pipl-comparison.json').write_text(json.dumps(pipldiff,indent=2))
    report={'candidate':candidate,'campaigns':campaigns,'totals':totals,'pipl_identical':True,
            'cpu':{'name':'AMD Ryzen 9 5900X 12-Core Processor','manufacturer':'AuthenticAMD','processor_id':'178BFBFF00A20F12'},
            'source_files':[identity(p) for p in sorted((OWN/'src').glob('*.rs'))],
            'qualification_passed':all(c['random_exact']>=200 and len(set(c['seeds']))>=2 and c['unresolved']==0 for c in totals.values()),
            'limitations':['AEXCompat only; native After Effects and macOS builds not performed','RCP estimate profile qualified on the recorded CPU; no claim for a different original-CPU approximation profile','PNG-promoted deep input campaign; native HDR and negative alpha fixtures not qualified','Active Noise Type 3 excluded/refused; zero-control identity copy remains supported','Original allocation-boundary nondeterminism is excluded only when demonstrated by identical-input replays','UI code compiled; native AE UI behavior unverified','Pure renderer has a conservative checked 1 GiB allocation budget; large-frame qualification not performed']}
    worker=Path('D:/Projects/01_Project/04_Tools/AEXCompat-wt-main/target/minihost-build/aex_worker.exe')
    if worker.exists():report['installed_worker_file']=identity(worker)
    (OWN/'validation-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(totals,indent=2));print('qualification_passed',report['qualification_passed'])
