#!/usr/bin/env python3
"""Sequential local release gate. Exit 0 means local evidence PASS, never AE exact."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
TICKET = 'R09-release-gate-v2'
SEEDS = (2026, 2027)
PLUGINS = dict(olmblur='OLMBlur', colorkeep='ColorKeep', olmcolorkey='OLMColorKey',
    olmdirectionalblur='OLMDirectionalBlur', olmdistancegradation='OLMDistanceGradation',
    olmkirakira='OLMKiraKira', olmsmoother2='OLMSmoother2', olmtoondilate='OLMToonDilate',
    radialblur='OLMRadialBlur', olmsmoother='OLMSmoother')
CACHE = Path.home()/'.cache/olm-emu'
WORKER = CACHE/'worker-F46-pow/aex-guest-worker'
BUNDLE_WORKER = CACHE/'worker-F47d/aex-guest-worker'

# Explicit snapshot of the 53-entry generic gate, selected from R05's measured
# 45 PASS entries. Exclusions are open findings, not passes or deleted tests.
SELECTED_TESTS = (
    'tests/test_colorkeep_generic_beta_20260820.py',
    'tests/test_colorkeep_roi_tile_beta_20260820.py',
    'tests/test_olmblur_generic_beta_lane_20260820.py',
    'tests/test_olmblur_generic_beta_sanitizers_20260820.py',
    'tests/test_olmblur_generic_classic_beta_20260822.py',
    'tests/test_olmblur_roi_halo_contract_20260820.py',
    'tests/test_olmcolorkey_generic_pixel_local_beta.py',
    'tests/test_olmcolorkey_generic_pixel_local_pairwise.py',
    'tests/test_olmcolorkey_generic_roi_tile.py',
    'tools/emulation/test_dblur_generic_pf8_geometry_beta_20260820.py',
    'tools/emulation/test_dblur_generic_deep_geometry_beta_20260820.py',
    'tools/emulation/test_dblur_generic_backonly_beta_20260821.py',
    'tools/emulation/test_dblur_generic_admission_budget_20260821.py',
    'tools/emulation/test_dblur_generic_roi_policy_20260820.py',
    'tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py',
    'tests/test_olmdistancegradation_smart_transactional_20260822.py',
    'tests/test_olmkirakira_generic_beta_lane_20260820.py',
    'tests/test_olmkirakira_generic_beta_sanitizers_20260820.py',
    'tests/test_olmkirakira_native_smoke_tuple_20260820.py',
    'tests/test_olmradialblur_generic_baseline_sanitizers_20260820.py',
    'tests/test_olmradialblur_generic_type3_sanitizers_20260820.py',
    'tests/test_olmradialblur_generic_budget_20260821.py',
    'tests/test_olmradialblur_size_noise_effectmain_20260821.py',
    'tests/test_olmradialblur_global_polar_smart_contract_20260820.py',
    'tests/test_olmsmoother_v1_generic_classic_beta_20260820.py',
    'tests/test_olmsmoother_v1_smart_beta_20260822.py',
    'tests/test_olmsmoother2_default_beta_lane_20260820.py',
    'tests/test_olmsmoother2_gamma_colors_beta_20260820.py',
    'tests/test_olmsmoother2_roi_fullframe_contract_20260820.py',
    'tests/test_olmtoondilate_generic_beta.py',
    'tests/test_olmtoondilate_roi_safety.py',
    'tests/test_olm_world_safety.py',
    'tests/test_olm_checked_allocation.py',
    'tests/test_olm_checked_rect.py',
    'tests/test_olm_roi_contract.py',
    'tests/test_olm_property_cases.py',
    'tests/test_olm_roi_tile_property.py',
    'tests/test_generate_aexcompat_oracle_campaign.py',
    'tests/test_run_aexcompat_reference_20260725.py',
    'tests/test_generic_beta_windows_oracle_handoff.py',
    'tests/test_ae_generalization_smoke.py',
    'tests/test_ae_png_completion.py',
    'tests/test_ae_batch_png_integrity.py',
    'tests/test_run_olm_generic_beta_gate.py',
    'tests/test_verify_mac_plugin_package_hash.py',
)
EXCLUDED_LEGACY_TESTS = {
    'tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py': 'operation-budget rejection contract (R07)',
    'tools/emulation/test_olmdirectionalblur_smart_cleanup_atomic_20260813.py': 'pre-allocation cleanup contract (R07)',
    'tests/test_olmdistancegradation_generic_production_beta_20260820.py': 'PF32 blurred-budget rejection contract (R07)',
    'tests/test_olmkirakira_mode3_ui_length_beta_20260821.py': 'zero-length rejection contract (R07)',
    'tests/test_olmkirakira_mode3_ui_windows_owner_20260821.py': 'native Windows owner evidence (R05/R07)',
    'tests/test_olmradialblur_generic_baseline_20260820.py': 'PF32 center-domain admission contract (R07)',
    'tests/test_beta_support_documentation.py': 'stale support documentation binding (R05/R07)',
    'tests/test_generic_beta_perf_smoke_runner.py': 'stale performance runner binding (R05/R07)',
}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text()) if Path(path).is_file() else {}


def owner(plugin):
    return 'classic' if plugin == 'olmsmoother' else 'smart'


def oracle(result, route):
    return result.get('oracles', {}).get(route, result.get('oracle', {}))


def guest_stop(value):
    # Never excuse harness errors, declaration drift, missing workers or Mac stops.
    diagnostic = value.get('diagnostic', '').lower()
    return (value.get('status') == 'budget' or
            (value.get('status') == 'reject' and any(token in diagnostic for token in
             ('guest', 'uc_err_', 'instruction limit', 'timeout', 'budget', 'invalid memory'))))


def has_stop(result):
    return any(guest_stop(oracle(result, route)) for route in result.get('routes', {}))


def persistent_stop_matches(observed, saved):
    """Only changed oracle-stop routes may substitute their saved reference hash."""
    if set(observed.get('routes', {})) != set(saved.get('routes', {})):
        return False
    stopped = False
    for route, actual in observed['routes'].items():
        current_oracle, old_oracle = oracle(observed, route), oracle(saved, route)
        if guest_stop(current_oracle):
            stopped = True
            expected = old_oracle.get('raw_sha256')
            if (old_oracle.get('status') != 'ok' or not expected or
                    actual.get('status') != 'uncompared' or actual.get('raw_sha256') != expected):
                return False
        elif actual != saved['routes'][route] or current_oracle != old_oracle:
            return False
    return stopped


def campaign_counts(report, plugin, expected):
    counts = Counter(E=0, M=0, R=0, U=0, errors=0)
    route = owner(plugin)
    rows = report.get('cases', [])
    for row in rows:
        result = row.get('result', {})
        status = result.get('routes', {}).get(route, {}).get('status')
        counts[{'exact':'E', 'mismatch':'M', 'no_write_violation':'M',
                'refuse':'R', 'refusal':'R', 'reject':'R'}.get(status, 'U')] += 1
        if row.get('worker_error') or row.get('status') == 'unresolved' or status in ('error', 'harness_error', None):
            counts['errors'] += 1
    complete = report.get('status') == 'complete' and report.get('completed') == expected and len(rows) == expected
    return dict(counts), complete and not counts['M'] and not counts['errors']


class Gate:
    def __init__(self, state, python, jobs=2):
        self.state, self.python = state, python
        self.env = {k:v for k,v in os.environ.items() if not k.startswith(('OLM_', 'DBLUR_', 'COLORKEEP_'))}
        self.env.update(OLM_TEST_JOBS=str(jobs), TMPDIR=str(state), TMP=str(state), TEMP=str(state),
                        PYTHONDONTWRITEBYTECODE='1', OLM_FUZZ_TEST_SCRATCH=str(state/'framework-scratch'))
        self.summary = dict(schema='olm-release-gate/2', started_utc=datetime.now(timezone.utc).isoformat(),
            git_head=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
            script_sha256=digest(__file__), seeds=list(SEEDS), n_per_seed=300, fuzz_jobs=1,
            OLM_TEST_JOBS=jobs, stages=[], commands=[], real_host=[
                {'item':item, 'status':'REQUIRES-REAL-HOST'} for item in
                ('installed identity', 'native host smoke', 'Windows owner evidence')],
            excluded_legacy_tests=EXCLUDED_LEGACY_TESTS,
            exclusion_evidence=['orchestra/reports/R05-regenerate-stale-bindings.md',
                                'orchestra/reports/R07-gate-contracts-and-bindings.md'])

    def save(self):
        (self.state/'summary.json').write_text(json.dumps(self.summary, indent=2)+'\n')

    def run(self, name, args, timeout=7200):
        log = self.state/(name+'.log')
        started = time.monotonic()
        with log.open('w') as stream:
            process = subprocess.Popen(list(map(str,args)), cwd=ROOT, env=self.env,
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except BaseException:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
        row = dict(name=name, command=list(map(str,args)), exit=code,
                   seconds=round(time.monotonic()-started,2), log=str(log.relative_to(ROOT)))
        self.summary['commands'].append(row)
        self.save()
        return code

    def stage(self, name, function):
        print('START', name, flush=True)
        try:
            details, passed = function()
        except Exception:
            details, passed = {'error':traceback.format_exc()}, False
        self.summary['stages'].append(dict(name=name, status='PASS' if passed else 'FAIL', **details))
        self.save()
        print('END', name, 'PASS' if passed else 'FAIL', flush=True)

    def framework(self):
        code = self.run('framework', [self.python, '-B', '-m', 'unittest', 'discover',
            '-s', 'tools/fuzz', '-p', 'test_*.py', '-v'])
        log = (self.state/'framework.log').read_text()
        found = re.search(r'Ran (\d+) tests', log)
        skipped = re.search(r'skipped=(\d+)', log)
        return dict(tests=int(found[1]) if found else 0, skipped=int(skipped[1]) if skipped else 0), code == 0 and bool(found)

    def build(self):
        pressure = self.run('memory-pressure', ['memory_pressure'])
        if pressure:
            return dict(bundles=0, error='memory_pressure failed; build not started'), False
        code = self.run('build', [self.python, '-B', 'tools/fuzz/build_F47_bundles.py',
                                 '--scratch', self.state/'bundles'])
        rows = []
        for name in PLUGINS.values():
            exe = self.state/f'bundles/xcode/{name}/products/{name}.plugin/Contents/MacOS/{name}'
            if exe.is_file():
                archs = subprocess.check_output(['lipo','-archs',str(exe)],text=True).split()
                rows.append(dict(plugin=name, sha256=digest(exe), architectures=archs))
        return dict(bundles=len(rows), executables=rows), code == 0 and len(rows)==10 and all(set(r['architectures'])=={'arm64','x86_64'} for r in rows)

    def fuzz(self, label, plugin, extra):
        report = self.state/(label+'.json')
        code = self.run(label, [self.python, '-B', 'tools/fuzz/run.py', '--plugin',plugin,
            '--jobs','1', '--budget-minutes','90', '--shrink-attempts','0','--shrink-seconds','0',
            '--scratch',self.state/'fuzz-scratch', '--corpus',self.state/'witnesses'/label,
            '--corpus-max-bytes','100000000', '--report',report, *extra])
        return code, read_json(report)

    def replays(self):
        groups = defaultdict(list)
        inventory = Counter({p:0 for p in PLUGINS})
        for path in sorted((ROOT/'tests/fuzz_corpus').rglob('*.json')):
            saved = read_json(path)
            plugin = saved['plugin']
            if plugin not in PLUGINS:
                raise ValueError('unknown corpus plugin: '+plugin)
            groups[plugin, path.parent].append(path)
            inventory[plugin] += 1
        rows = []; counts = Counter(PASS=0, FAIL=0, **{'ORACLE-STOP':0})
        for i, ((plugin, directory), paths) in enumerate(sorted(groups.items())):
            _, report = self.fuzz(f'replay-{i:02d}-{plugin}',plugin,['--replay',directory])
            observed = {r['path']:r for r in report.get('replays', [])}
            for path in paths:
                row = observed.get(str(path), {})
                result = row.get('result', {})
                verdict = 'PASS' if row.get('matches_saved') else 'FAIL'
                retry = None
                if not row.get('matches_saved') and has_stop(result):
                    retry = f'retry-{len(rows):04d}-{plugin}'
                    _, retried = self.fuzz(retry,plugin,['--replay',path,'--case-timeout','120'])
                    rr = retried.get('replays', [])
                    verdict = 'FAIL'
                    if len(rr)==1 and retried.get('status')=='replay_complete':
                        if has_stop(rr[0]['result']):
                            if persistent_stop_matches(rr[0]['result'], read_json(path)['result']):
                                verdict = 'ORACLE-STOP'
                        elif rr[0]['matches_saved']:
                            verdict = 'PASS'
                counts[verdict] += 1
                rows.append(dict(path=str(path.relative_to(ROOT)), sha256=digest(path), verdict=verdict,
                                 retry=retry, error=report.get('error') if not row else None))
        (self.state/'replay-verdicts.json').write_text(json.dumps(rows,indent=2)+'\n')
        return dict(counts=dict(counts), corpus_by_plugin=dict(inventory), total=len(rows),
            empty_corpora=[p for p,n in inventory.items() if n==0],
            verdicts=str((self.state/'replay-verdicts.json').relative_to(ROOT))), bool(rows) and not counts['FAIL']

    def campaigns(self):
        rows = []; passed = True; totals = Counter()
        for plugin in PLUGINS:
            for seed in SEEDS:
                code, report = self.fuzz(f'fresh-{plugin}-{seed}',plugin,
                    ['--seed',str(seed),'--n','300','--worker',WORKER])
                counts, good = campaign_counts(report,plugin,300)
                passed &= code == 0 and good
                totals.update(counts)
                rows.append(dict(plugin=plugin, seed=seed, route=owner(plugin), counts=counts,
                                 status='PASS' if code==0 and good else 'FAIL', report_status=report.get('status')))
        return dict(counts=dict(totals), campaigns=rows), passed

    def bundles(self):
        state = self.state/'f47d'; state.mkdir()
        (state/'bundles').symlink_to(self.state/'bundles',target_is_directory=True)
        code = self.run('f47d',[self.python,'-B','tools/fuzz/verify_F47d.py','--state',state,
            '--worker',BUNDLE_WORKER,'--candidates','plugin-bundle','--n','100'], timeout=15000)
        totals=Counter(); rows=[]; passed=code==0
        for plugin in PLUGINS:
            report=read_json(state/(plugin+'-plugin-bundle.json'))
            counts, good=campaign_counts(report,plugin,100)
            totals.update(counts); passed &= good
            rows.append(dict(plugin=plugin, counts=counts, status='PASS' if good else 'FAIL'))
        code=self.run('f51',[self.python,'-B','tools/fuzz/verify_F51.py','--state',self.state/'f51',
            '--bundles',self.state/'bundles','--n','100','--jobs','1'], timeout=15000)
        report=read_json(self.state/'f51/summary.json')
        expected=1000+sum(1 for _ in (ROOT/'tests/fuzz_corpus').rglob('*.json'))
        f51=report.get('totals',{})
        good=code==0 and sum(f51.values())==expected and f51.get('difference',0)==0
        return dict(F47d=dict(counts=dict(totals), plugins=rows), F51=dict(counts=f51,expected=expected)), passed and good

    def tests(self):
        rows=[]
        for i,path in enumerate(SELECTED_TESTS):
            args=[self.python,'-B',path] if path.startswith('tools/') else [self.python,'-B',
                'scripts/run_olm_generic_beta_gate.py','--run-test-file',ROOT/path]
            code=self.run(f'unit-{i:02d}',args,timeout=900)
            rows.append(dict(test=path,sha256=digest(ROOT/path),exit=code,status='PASS' if code==0 else 'FAIL'))
        return dict(selected=rows,counts=dict(Counter(r['status'] for r in rows))), all(r['exit']==0 for r in rows)

    def static(self):
        sys.path.insert(0,str(ROOT/'tools/emulation'))
        from audit_route_flags_F18 import pe_pipls, mac_pipls
        import pefile
        originals={r['plugin']:r for r in read_json(ROOT/'reports/route_flags_F18_after.json')['plugins']}
        rows=[]
        for name in PLUGINS.values():
            code=self.run('settings-'+name,['xcodebuild','-project',ROOT/f'mac/{name}/Mac/{name}.xcodeproj',
                '-configuration','Release','-showBuildSettings','-json'])
            settings=read_json(self.state/('settings-'+name+'.log'))
            targets=[s['buildSettings'] for s in settings]
            configs=bool(targets) and all(
                all(flag in s.get(key,'').split() for key in ('OTHER_CFLAGS','OTHER_CPLUSPLUSFLAGS')
                    for flag in ('-ffp-contract=off','-fno-fast-math')) and
                set(s.get('ARCHS','').split())=={'arm64','x86_64'} and
                s.get('MACOSX_DEPLOYMENT_TARGET')=='11.0' for s in targets)
            old=originals[name]; aex=Path(old['aex_path'])
            original=pe_pipls(pefile.PE(str(aex)))
            resources=list((self.state/f'bundles/xcode/{name}/products/{name}.plugin/Contents/Resources').glob('*.rsrc'))
            mac=[p for resource in resources for p in mac_pipls(resource)]
            flags=lambda records: sorted((r['out_flags'],r['out_flags2']) for r in records)
            equal=bool(mac) and flags(original)==flags(mac) and digest(aex)==old['aex_sha256']
            rows.append(dict(plugin=name, release_config=configs and code==0, pipl_equal=equal,
                original_flags=flags(original), mac_flags=flags(mac), aex_sha256=digest(aex)))
        known=ROOT/'notes/KNOWN_ORIGINAL_BUGS.md'
        return dict(plugins=rows, count=len(rows), known_original_bugs_sha256=digest(known)), all(r['release_config'] and r['pipl_equal'] for r in rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,default=ROOT/'orchestra/state'/TICKET/'run')
    parser.add_argument('--python',type=Path,default=MAIN/'tools/emulation/.venv/bin/python3')
    parser.add_argument('--jobs', type=int, choices=(1, 2), default=2)
    args=parser.parse_args()
    if Path(sys.executable).absolute() != args.python.absolute():
        os.execv(str(args.python), [str(args.python), '-B', str(Path(__file__).resolve()), *sys.argv[1:]])
    if sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE'):
        parser.error('optimized Python is not allowed')
    state=args.state.resolve()
    if not state.is_relative_to((ROOT/'orchestra/state').resolve()):
        parser.error('state must be inside this worktree orchestra/state')
    state.mkdir(parents=True,exist_ok=False)
    gate=Gate(state,args.python,args.jobs)
    try:
        for name,function in [('framework',gate.framework),('build',gate.build),('corpus',gate.replays),
            ('fresh-seeds',gate.campaigns),('bundle-checks',gate.bundles),('plugin-tests',gate.tests),('static',gate.static)]:
            gate.stage(name,function)
    finally:
        gate.summary['local_gate_pass']=len(gate.summary['stages'])==7 and all(r['status']=='PASS' for r in gate.summary['stages'])
        gate.summary['release_authorized']=False
        gate.summary['finished_utc']=datetime.now(timezone.utc).isoformat()
        # Bundles are regenerable candidates, never installed reference oracles.
        shutil.rmtree(state/'bundles/xcode',ignore_errors=True)
        gate.save()
    return 0 if gate.summary['local_gate_pass'] else 1


if __name__=='__main__':
    raise SystemExit(main())
