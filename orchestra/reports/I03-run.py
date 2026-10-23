#!/usr/bin/env python3
"""Sequential I03 verification with scratch-confined environment and logs."""
import json, os, re, shutil, signal, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/I03-integration-check'
MAIN=ROOT.parent.parent
S.mkdir(parents=True,exist_ok=True)
for name in ('F17-fuzz-per-route-oracle','F23-corpus-rebaseline-all','T04-fuzz-adapters-all-plugins','F36-fixture-runner-worktree-and-triage','F22-smoother-classifier-stack-ub'):
    target=S/'compat-scratch'/name
    target.mkdir(parents=True,exist_ok=True)
    link=ROOT/'orchestra/state'/name
    if not link.exists(): link.symlink_to(target,target_is_directory=True)
PY=str(MAIN/'tools/emulation/.venv/bin/python3')
ENV=dict(os.environ, OLM_TEST_JOBS='2', PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(S), TMP=str(S), TEMP=str(S), OLM_MAIN_ASSETS=str(MAIN), OLM_FUZZ_TEST_SCRATCH=str(S/'framework'))
def retain_generated(name):
    paths=subprocess.check_output(['git','diff','--name-only','--','refs/conformance'],cwd=ROOT,text=True).splitlines()
    if not paths: return
    dest=S/'generated-evidence'/name
    dest.mkdir(parents=True,exist_ok=True)
    with (dest/'changes.patch').open('wb') as out:
        subprocess.run(['git','diff','--',*paths],cwd=ROOT,stdout=out,check=True)
    for rel in paths:
        target=dest/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        if (ROOT/rel).exists(): shutil.copy2(ROOT/rel,target)
    subprocess.run(['git','restore','--worktree','--',*paths],cwd=ROOT,check=True)
def run(name,argv,timeout=3600):
    start=time.time()
    with (S/(name+'.log')).open('w') as log:
        proc=subprocess.Popen(argv,cwd=ROOT,env=ENV,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try: code=proc.wait(timeout=timeout)
        except BaseException:
            os.killpg(proc.pid,signal.SIGTERM)
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL); proc.wait()
            raise
    retain_generated(name)
    row=dict(name=name,command=argv,exit=code,seconds=round(time.time()-start,3))
    with (S/'commands.jsonl').open('a') as out: out.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)
    return code
if __name__=='__main__':
    stage=sys.argv[1]
    if stage=='gates':
        run('release',[PY,'orchestra/reports/I03-release.py'],14400)
        run('generic',[PY,'scripts/run_olm_generic_beta_gate.py','--report',str(S/'generic.json')],14400)
        for path in sorted((ROOT/'tools/fuzz').glob('test_*.py')):
            if path.stem=='test_colorkey_existing_F20': continue
            run('framework-'+path.stem,[PY,str(path)])

    elif stage=='units':
        if not (S/'python-deps/pytest/__init__.py').exists():
            run('pytest-install',[PY,'-m','pip','--disable-pip-version-check','install','--target',str(S/'python-deps'),'--cache-dir',str(S/'pip-cache'),'--no-compile','-r',str(ROOT/'orchestra/reports/I03-pytest-requirements.txt')])
        ENV['PYTHONPATH']=os.pathsep.join([str(S/'python-deps'),str(ROOT),ENV.get('PYTHONPATH','')])
        ENV['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
        ENV['OLM_FUZZ_INTEGRATION']='1'
        for path in sorted((ROOT/'tools/fuzz').glob('test_*.py')):
            if path.stem=='test_colorkey_existing_F20': continue
            run('integration-'+path.stem,[PY,str(path)])
        run('framework-F20-main',[PY,'-c',"import sys; from pathlib import Path; sys.path.insert(0,'tools/fuzz'); import test_colorkey_existing_F20 as m; m.SCRATCH=Path("+repr(str(S/'f20-tests'))+"); m.main()"])
        files=[p for p in (ROOT/'tests').glob('test_*.py') if any(n in p.name for n in ('olm','radialblur','directionalblur','colorkeep','colorkey','smoother','toondilate','kirakira','distancegradation','directional_radial'))]
        reused={}
        for row in json.loads((S/'fixtures/results.json').read_text()):
            if not row.get('log'): continue
            if not re.search(r'Ran [1-9][0-9]* tests?',Path(row['log']).read_text(errors='replace')): continue
            for arg in row['command'][1:]:
                rel=('tests/'+arg[6:]+'.py') if arg.startswith('tests.test_') else arg
                if rel.startswith(str(ROOT)+'/'): rel=rel[len(str(ROOT))+1:]
                if rel.startswith('tests/test_') and rel.endswith('.py'):
                    reused[rel]=dict(origin='release fixtures',exit=row['returncode'],log=row['log'])
        if (S/'generic.json').exists():
            for row in json.loads((S/'generic.json').read_text()).get('entries',[]):
                if row.get('exit_code') is not None and row['test'].startswith('tests/') and 'unsupported parameters' not in json.dumps(row):
                    reused[row['test']]=dict(origin='generic gate',exit=row['exit_code'],status=row['status'])
        inventory=[dict(path=str(p.relative_to(ROOT)),reused=reused.get(str(p.relative_to(ROOT)))) for p in sorted(files)]
        (S/'unit-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
        for path in sorted(files):
            if str(path.relative_to(ROOT)) in reused: continue
            code=run('unit-'+path.stem,[PY,'-m','pytest','-q','-p','no:cacheprovider','--basetemp',str(S/'pytest-temp'),str(path)],14400)
            if code==5: run('unit-script-'+path.stem,[PY,str(path)],14400)
    elif stage=='unit-followup':
        rows=[json.loads(x) for x in (S/'commands.jsonl').read_text().splitlines()]
        for row in rows:
            if row['name'].startswith('unit-') and row['exit']==5:
                path=Path(row['command'][-1])
                run('unit-script-'+path.stem,[PY,str(path)],14400)
    elif stage in ('replay','replay-nested'):
        corpus_root=ROOT/'tests/fuzz_corpus'
        paths={p.parent for p in corpus_root.rglob('*.json')}
        if stage=='replay-nested': paths={p for p in paths if p.parent!=corpus_root}
        else: paths|={p for p in corpus_root.iterdir() if p.is_dir()}
        for path in sorted(paths):
            if not path.is_dir(): continue
            files=sorted(path.glob('*.json'))
            plugin=json.loads(files[0].read_text())['plugin'] if files else path.name
            run('replay-'+path.name,[PY,'tools/fuzz/run.py','--plugin',plugin,'--replay',str(path),'--jobs','2','--budget-minutes','180','--scratch',str(S/'replay-scratch'),'--report',str(S/('replay-'+path.name+'.json'))],14400)
            report=json.loads((S/('replay-'+path.name+'.json')).read_text())
            for index,row in enumerate(report.get('replays',[])):
                if row['matches_saved']: continue
                saved=json.loads(Path(row['path']).read_text())
                original=json.dumps([row['result'].get('oracles'),row['result'].get('oracle'),saved['result'].get('oracles'),saved['result'].get('oracle')])
                if 'execution stopped before' not in original: continue
                run('retry-'+path.name+'-'+str(index),[PY,'tools/fuzz/run.py','--plugin',plugin,'--replay',row['path'],'--case-timeout','120','--jobs','1','--budget-minutes','15','--scratch',str(S/'retry-scratch'),'--report',str(S/('retry-'+path.name+'-'+str(index)+'.json'))],3600)
    elif stage=='fresh':
        for plugin in ('olmblur','colorkeep','olmcolorkey','olmdirectionalblur','olmdistancegradation','olmkirakira','olmsmoother2','olmtoondilate','radialblur','olmsmoother'):
            run('fresh-'+plugin,[PY,'tools/fuzz/run.py','--plugin',plugin,'--seed','777','--n','300','--jobs','2','--budget-minutes','180','--shrink-attempts','0','--shrink-seconds','0','--scratch',str(S/'fresh-scratch'),'--report',str(S/('fresh-'+plugin+'.json')),'--corpus',str(S/'witnesses'/plugin),'--corpus-max-bytes','50000000'],14400)
    elif stage=='bundles':
        run('build-bundles',[PY,'tools/fuzz/build_F47_bundles.py','--scratch',str(S/'bundles')],14400)
        run('verify-F47d',[PY,'tools/fuzz/verify_F47d.py','--state',str(S),'--worker',str(Path.home()/'.cache/olm-emu/worker-F47d/aex-guest-worker'),'--candidates','plugin-bundle','--n','100'],14400)
        run('verify-F51',[PY,'tools/fuzz/verify_F51.py','--state',str(S/'F51'),'--bundles',str(S/'bundles'),'--n','100'],14400)

    elif stage=='classify-followup':
        ENV['I03_BISECT_LABEL']='link-bisect-extra-F31'
        run('link-bisect-extra-F31',[PY,'orchestra/reports/I03-bisect-links.py','--boundary','1979c3a9','--tests','tests/test_olmblur_generic_beta_sanitizers_20260820.py','@edge-fade','@edge-intersection'],14400)
        ENV['I03_BISECT_LABEL']='link-bisect-extra-F46'
        run('link-bisect-extra-F46',[PY,'orchestra/reports/I03-bisect-links.py','--boundary','1a5b279e','--tests','tests/test_olmsmoother2_gamma_colors_beta_20260820.py'],14400)
        ENV['I03_BISECT_LABEL']='policy-bisect'
        ENV['I03_BISECT_MODE']='exit'
        run('policy-bisect',[PY,'orchestra/reports/I03-bisect-links.py','--tests','tests/test_colorkeep_generic_beta_20260820.py','tests/test_colorkeep_roi_tile_beta_20260820.py','tests/test_olmblur_generic_beta_lane_20260820.py','tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py','tests/test_olmradialblur_generic_budget_20260821.py'],14400)
        run('release-component-audit',[PY,'orchestra/reports/I03-audit-components.py'])
        for name in ('test_beta_support_documentation','test_generic_beta_perf_smoke_runner','test_run_olm_generic_beta_gate'):
            run('diagnostic-'+name,[PY,'scripts/run_olm_generic_beta_gate.py','--run-test-file',str(ROOT/'tests'/(name+'.py'))])

    elif stage=='classify-warp':
        ENV['I03_BISECT_LABEL']='link-bisect-F45'
        run('link-bisect-F45',[PY,'orchestra/reports/I03-bisect-links.py','--boundary','d246aef8','--tests','tools/emulation/test_olmkirakira_mode3_default50_canonical_actual_aex_20260810.py','tools/emulation/test_olmkirakira_mode3_geometry_generalization_actual_aex_20260810.py','tools/emulation/test_olmkirakira_mode4_production_boundary_20260805.py','tools/emulation/test_olmkirakira_mode4_canonical_angles_actual_aex_20260810.py','tools/emulation/test_olmkirakira_mode4_cropped_typed_installed_20260805.py','tools/emulation/test_olmkirakira_warp_production_boundary_20260805.py'],14400)

    elif stage=='parameter-ui':
        run('parameter-ui-full',[PY,'scripts/run_olm_parameter_ui_gate_20260806.py','--report',str(S/'parameter-ui-full.json')])
