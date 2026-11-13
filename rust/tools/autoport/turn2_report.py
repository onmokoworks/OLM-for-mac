"""Rebuild the durable qualification summary from retained evidence; no new calls."""
import argparse,collections
from pathlib import Path
import autoport as a

def budget_valid(ledger):
    calls=ledger['calls']
    return (len(calls)<=60 and all(n<=4 for n in collections.Counter(c['function'] for c in calls).values())
        and all(c.get('total_attempt_seconds',float('inf'))<=300 for c in calls))

def report(root):
    ledger=a.read(root/'budget.json')
    result={'schema_version':1,'budget_valid':budget_valid(ledger),'codex_calls':len(ledger['calls']),
      'generation_seconds':sum(c['generation_seconds'] for c in ledger['calls']),
      'attempt_seconds':sum(c['total_attempt_seconds'] for c in ledger['calls']),
      'functions':ledger['calls'],'plugins':{},'native_admission':{}}
    for name in ['toon','color']:
        s=a.read(root/f'{name}-full/oracle/summary.json')
        p=a.read(root/f'{name}-full/process/process.json')
        lookup=a.read(root/f'{name}-lookup.json')
        qualified=[v for v in lookup['port_work'] if v['port_status']=='already-covered']
        result['plugins'][name]={'verdict':s['verdict'],'full':s['full'],
          'candidate_identity_valid':a.digest(s['candidate']['path'])==s['candidate']['sha256'],
          'reference_identity_valid':a.digest(s['reference']['path'])==s['reference']['sha256'],
          'inventory_diff':s['inventory_diff'],'routes':s['render_summary']['routes'],
          'oracle_seconds':p['seconds'],'cleanup_verified':p['cleanup_verified'],
          'funcdb_qualified_target_mappings_excluded':[v['rva'] for v in qualified],
          'shared_known_functions_imported':0}
    paths=['replay8','replay16','replay32']
    paths += [f'capture{d}-{kind}-{lane}' for d in [8,16,32] for kind in ['zero','preview','single'] for lane in ['original','rust']]
    paths += [f'generation/01-toon-worker/capture{d}' for d in [8,16,32]]
    paths += [f'color-replay{d}' for d in [8,16,32]]
    for path in paths:
        p=root/path/'comparison.json'
        result['native_admission'][path]=a.read(p).get('exact',False) if p.exists() else False
    result['complete']=(result['budget_valid'] and all(result['native_admission'].values()) and
        all(p['verdict']=='PASS' and p['full'] and p['candidate_identity_valid'] and p['reference_identity_valid'] and p['cleanup_verified'] for p in result['plugins'].values()))
    a.write(root/'qualification.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);x=p.parse_args()
    result=report(x.root.resolve());print({k:result[k] for k in ['complete','codex_calls','generation_seconds','attempt_seconds']})
    raise SystemExit(0 if result['complete'] else 2)
