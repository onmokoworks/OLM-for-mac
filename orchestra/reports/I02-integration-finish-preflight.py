#!/usr/bin/env python3
"""Read-only safety preflight; never imports or executes emulator campaigns.

The dispatch experiment executes only the test's __main__ block, with main
replaced by a sentinel. It is not an end-to-end emulator validation.
"""
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import types

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'scripts/run_olm_mac_fixed_fixture_regression_20260805.py'
TARGET = 'tools/emulation/test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811.py'
FIX = '317e3ae9b79470034bfa0920b604d5e9a56b3dc2'


def dispatch(source, action):
    tree = ast.parse(source)
    block = next(n for n in tree.body if isinstance(n, ast.If)
                 and '__name__' in ast.unparse(n.test))
    calls = []
    stderr = io.StringIO()
    fake_sys = types.SimpleNamespace(
        argv=[TARGET, action, '2.0', '30.0', 'unused-output.pkl'], stderr=stderr)
    namespace = {'__name__': '__main__', 'sys': fake_sys,
                 'os': types.SimpleNamespace(environ={}),
                 'main': lambda: calls.append('campaign main reached') or 99}
    code = compile(ast.Module(body=[block], type_ignores=[]), TARGET, 'exec')
    try:
        with contextlib.redirect_stderr(stderr):
            exec(code, namespace)
    except SystemExit as exc:
        return {'exit': exc.code, 'campaign_main_calls': len(calls),
                'stderr': stderr.getvalue().strip()}
    raise AssertionError('dispatch failed to exit')


def main():
    findings = []
    commands = 0
    for node in ast.walk(ast.parse(RUNNER.read_text())):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == 'Lane'):
            continue
        lane = ast.literal_eval(node.args[0])
        for command in node.args[1].elts:
            commands += 1
            script = command.elts[1]
            if not (isinstance(script, ast.Constant) and isinstance(script.value, str)
                    and script.value.endswith('.py')):
                continue
            path = ROOT / script.value
            if not path.is_file():
                continue
            source = path.read_text()
            for call in ast.walk(ast.parse(source)):
                if not isinstance(call, ast.Call):
                    continue
                for kw in call.keywords:
                    if (kw.arg == 'max_workers' and isinstance(kw.value, ast.Constant)
                            and isinstance(kw.value.value, int) and kw.value.value > 2):
                        findings.append({'lane': lane, 'script': script.value,
                                         'line': call.lineno, 'max_workers': kw.value.value,
                                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    old = subprocess.check_output(['git', 'show', f'{FIX}^:{TARGET}'], cwd=ROOT, text=True)
    current = (ROOT / TARGET).read_text()
    experiments = []
    for action in ('--zoom-production', '--rotation-production'):
        before, after = dispatch(old, action), dispatch(current, action)
        assert before['campaign_main_calls'] == 1 and before['exit'] == 99
        assert after['campaign_main_calls'] == 0 and after['exit'] == 2
        experiments.append({'action': action, 'before_fix': before, 'current': after})
    siblings = []
    for effect in ('rotation', 'zoom'):
        name = f'tools/emulation/test_olmradialblur_{effect}_pf32_ellipse_actual_aex_20260811.py'
        result = dispatch((ROOT / name).read_text(), '--production')
        assert result['campaign_main_calls'] == 0 and result['exit'] == 2
        siblings.append({'script': name, 'action': '--production', 'current': result,
                         'sha256': hashlib.sha256((ROOT / name).read_bytes()).hexdigest()})
    print(json.dumps({
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'runner_sha256': hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
        'target_sha256': hashlib.sha256((ROOT / TARGET).read_bytes()).hexdigest(),
        'enumerated_commands': commands,
        'over_limit_sites': len(findings),
        'over_limit_files': len({f['script'] for f in findings}),
        'findings': findings, 'dispatch_experiments': experiments,
        'protected_sibling_dispatch': siblings,
        'status': 'static_preflight_pass' if not findings else 'over_limit_pool_found',
        'measurement_boundary': 'Static literal pool sizes; no runtime descendant or RSS measurements.',
    }, indent=2))


if __name__ == '__main__':
    main()
