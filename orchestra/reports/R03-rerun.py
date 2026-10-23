#!/usr/bin/env python3
"""Rerun exactly the I03 missing-link commands with confined temporary outputs."""
import argparse, json, os, signal, subprocess, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
S = ROOT/'orchestra/state/R03-harness-ucrt-link'
MAIN = ROOT.parent.parent
PY = str(MAIN/'tools/emulation/.venv/bin/python3')
S.mkdir(parents=True, exist_ok=True)
if subprocess.check_output(['git','diff','--name-only','HEAD','--','refs/conformance'],cwd=ROOT,text=True).strip():
    raise SystemExit('Start with clean refs/conformance; refusing to overwrite existing edits')
env = dict(os.environ, OLM_TEST_JOBS='2', TMPDIR=str(S), TMP=str(S), TEMP=str(S),
           PYTHONDONTWRITEBYTECODE='1', OLM_MAIN_ASSETS=str(MAIN), PYTHONPATH=str(ROOT))
old = str(MAIN/'worktrees/I03-integration-check')
rows = [r for r in json.loads((ROOT/'orchestra/reports/I03-classification.json').read_text())['failures']
        if r['category']=='a: UCRT link dependency' or r['category'].startswith('mixed:')]
rows += [dict(key='F20', command=[PY,'-c',
    "import sys; from pathlib import Path; sys.path.insert(0,'tools/fuzz'); import test_colorkey_existing_F20 as m; m.SCRATCH=Path("+repr(str(S/'f20-tests'))+"); m.main()"])]
manifest=json.loads((ROOT/'refs/conformance/olm_parameter_ui_gate_manifest_20260806.json').read_text())
for r in manifest['plugins']:
    if r['plugin'] in ('OLMDirectionalBlur','OLMDistanceGradation','OLMRadialBlur'):
        rows.append(dict(key='parameter-ui-'+r['plugin'],command=[PY,str(ROOT/r['runner'])]))
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only', type=int, nargs='+', help='Rerun selected zero-based records')
parser.add_argument('--observe-failures', action='store_true')
options=parser.parse_args()
existing = {r['key']:r for r in json.loads((S/'results.json').read_text())} if options.only and (S/'results.json').exists() else {}
results=[]
for index,r in enumerate(rows):
    if options.only and index not in options.only:
        if r['key'] in existing: results.append(existing[r['key']])
        continue
    command=[a.replace(old,str(ROOT)) for a in r['command']]
    prefix=('observed-' if options.observe_failures else '')+f'{index:03d}'
    log=S/(prefix+'.log'); events=S/(prefix+'-links.jsonl')
    if options.observe_failures:
        env['R03_DIAGNOSTICS']=str(S/'diagnostics'/str(index))
        command=[command[0], str(ROOT/'orchestra/reports/R03-probe-failure.py'), *command[1:]]
    if events.exists(): events.unlink()
    begin=time.monotonic()
    with log.open('w') as out:
        proc=subprocess.Popen(command,cwd=ROOT,env=dict(env,OLM_UCRT_LINK_LOG=str(events)),stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        try: code=proc.wait(timeout=900)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM);proc.wait();code=124
    # Legacy generators write pinned evidence. Retain their output, restore original bytes.
    paths=subprocess.check_output(['git','diff','--name-only','--','refs/conformance'],cwd=ROOT,text=True).splitlines()
    for rel in paths:
        target=S/'generated'/str(index)/rel;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/rel).read_bytes())
        original=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)
        (ROOT/rel).write_bytes(original)
    links=[json.loads(x) for x in events.read_text().splitlines()] if events.exists() else []
    result=dict(key=r['key'],command=command,exit=code,seconds=round(time.monotonic()-begin,2),
                log=log.name,links=len(links),link_failures=sum(x['exit']!=0 for x in links))
    results.append(result)
    (S/('observed-results.json' if options.observe_failures else 'results.json')).write_text(json.dumps(results,indent=2)+'\n')
    print(f"{index:03d} {r['key']}: exit={code} links={len(links)} failed={result['link_failures']}",flush=True)

(S/('observed-results.json' if options.observe_failures else 'results.json')).write_text(json.dumps(results,indent=2)+'\n')
