#!/usr/bin/env python3
"""Evidence inventory: observed error class, F40 cross-reference, and proven boundaries."""
import collections, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/I03-integration-check'
def normalized(command):
    command=list(command)
    if command and Path(command[0]).name.lower().startswith('python'): command=command[1:]
    return tuple(str(x).removeprefix(str(ROOT)+'/') for x in command)
def read(path):return json.loads(path.read_text()) if path.exists() else {}
f40={normalized(r['command']):r for r in read(ROOT/'orchestra/reports/F40-adjudication.json')['commands']}
boundaries={}
for path in S.glob('*bisect*/results.json'):
    for row in read(path).get('boundaries',[]):
        if row['status']=='bisected': boundaries[row['test']]=row
rows=[]
def classify(row,text,key):
    old=f40.get(normalized(row.get('command',[])))
    symbols=sorted(set(re.findall(r'"(_ucrt_[a-z0-9_]+)"',text)))
    if symbols and 'linker command failed' in text: category='a: UCRT link dependency'
    elif old and old['category']=='b':category='b: listed F40 binding'
    elif old:category='listed F40 unresolved input/contract'
    elif any(x in text for x in ('FileNotFoundError','No such file or directory','missing test:', 'installed plugin identity mismatch')):category='unresolved input/identity'
    elif any(x in text for x in ('identity drift','identity mismatch','source_hash','source_sha256','sha256 mismatch','runner identity','documentation drift','repository_source identity')):category='binding/contract (not automatically causal)'
    else:category='unclassified assertion/runtime'
    lines=text.splitlines();signals=[x[:700] for x in lines if any(k in x for k in ('Error:', 'FAIL:', 'AssertionError','Undefined symbols','_ucrt_','mismatch','drift','negative rc','budget probe'))]
    entry=dict(key=key,category=category,command=row.get('command'),exit=row.get('returncode',row.get('exit_code')),missing_symbols=symbols,evidence=signals[-6:],log=row.get('log'),F40_index=old['index'] if old else None,F40_note=old['note'] if old else None)
    test=row.get('test')
    if test in boundaries:entry['bisect']=boundaries[test]
    rows.append(entry)
for index,row in enumerate(read(S/'fixtures/results.json')):
    if row['returncode']==0:continue
    text=Path(row['log']).read_text(errors='replace') if row.get('log') else row.get('error','')
    command=normalized(row['command']);test=next((x for x in command if x.endswith('.py')),None)
    classify(dict(row,test=test),text,'fixture-'+str(index).zfill(3))
for row in read(S/'generic.json').get('entries',[]):
    if row['status']=='PASS':continue
    classify(row,row.get('stdout','')+'\n'+row.get('stderr',''),'generic:'+row['test'])
# Supplemental full diagnostics and adjacent revision controls resolve truncated gate tails.
for row in rows:
    key=row['key']; test=key.removeprefix('generic:')
    if key in ('fixture-169','fixture-170'):
        row['category']='a: UCRT link dependency'
        row['bisect']=boundaries['@edge-fade' if key.endswith('169') else '@edge-intersection']
        row['note']='Wrapper reports mismatch; retained generated report has four failed production children and zero matching planes. Compile-only adjacent controls identify the link failure.'
    if test in boundaries:
        row['bisect']=boundaries[test]
        row['category']='a: admission assertion drift' if boundaries[test]['merge'].startswith(('8857fbc','7a0cd797')) else 'a: UCRT link dependency'
    if key.endswith('test_beta_support_documentation.py'):
        row['category']='b: documentation/source/performance bindings'
        row['note']='Full diagnostic: 19 tests, four failures; also reported by I02.'
    if key.endswith('test_generic_beta_perf_smoke_runner.py'):
        row['category']='mixed: performance bindings and F31 link dependency'
        row['note']='Full diagnostic preserves executable-prefix/Kira command binding errors and selected Kira harness link failure; shared UCRT dependency boundary F31.'
    if key.endswith('test_olmkirakira_mode3_ui_windows_owner_20260821.py'):
        row['category']='b: Windows owner evidence binding'
    if row['category']=='a: UCRT link dependency' and 'bisect' not in row:
        row['shared_cause']='F31 (1979c3a9): observed missing UCRT symbols; representative adjacent controls in link-bisect/results.json. No claim of historical whole-test success.'
result=dict(counts=dict(collections.Counter(r['category'] for r in rows)),failures=rows,boundaries=boundaries)
(S/'classification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['counts'],sort_keys=True))
