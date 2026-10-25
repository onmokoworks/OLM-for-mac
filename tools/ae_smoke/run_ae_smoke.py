#!/usr/bin/env python3
"""AE 2026: one GUI project build, then serial aerender and raw I/O checks."""
import argparse
import json
import os
import plistlib
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / 'orchestra/state/A01c-real-ae-render-aerender'
APP = Path('/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app')
PLUGINS = ['OLMBlur', 'ColorKeep', 'OLMColorKey', 'OLMDirectionalBlur',
           'OLMDistanceGradation', 'OLMKiraKira', 'OLMSmoother2', 'OLMToonDilate',
           'OLMRadialBlur', 'OLMSmoother']


def capture(cmd):
    return subprocess.check_output(cmd, text=True)


def running():
    return [line.strip().split(None, 1)[0]
            for line in capture(['ps', '-axo', 'pid=,comm=']).splitlines()
            if re.search(r'MacOS/After Effects$', line)]


def screen_locked():
    data = plistlib.loads(subprocess.check_output(['ioreg', '-n', 'Root', '-d1', '-a']))
    root = data[0] if isinstance(data, list) else data
    users = root.get('IOConsoleUsers', [])
    for user in users:
        if user.get('CGSSessionScreenIsLocked') is True:
            return True
    console = [user for user in users
               if user.get('kCGSSessionOnConsoleKey') is True
               and user.get('kCGSessionLoginDoneKey') is True]
    if len(console) == 1 and 'CGSSessionScreenIsLocked' not in console[0]:
        return False
    raise RuntimeError('Cannot establish screen lock state; launch refused')


def wait_unlocked(state):
    log_path = state / 'screen-lock.log'
    # Preserve the original deadline across worker/orchestrator restarts.
    started = time.time()
    if log_path.exists():
        with log_path.open() as previous:
            first = previous.readline().split()
        if first:
            started = float(first[0])
    deadline = time.monotonic() + max(0, started + 12 * 3600 - time.time())
    while True:
        locked = screen_locked()
        with log_path.open('a') as log:
            log.write(f'{time.time():.3f} locked={locked}\n')
        if not locked:
            return
        if time.monotonic() >= deadline:
            raise RuntimeError('Screen remained locked for 12 hours; no AE launch')
        print('Screen locked; waiting five minutes without launching AE', flush=True)
        time.sleep(min(300, max(0, deadline - time.monotonic())))


def preflight(state):
    deadline = time.monotonic() + 7200
    while running() or any(re.search(r'/aerender$', line)
                           for line in capture(['ps', '-axo', 'pid=,comm=']).splitlines()):
        if time.monotonic() >= deadline:
            raise RuntimeError('AE busy for 2 hours; existing process untouched')
        print('AE busy; waiting (no signal sent)', flush=True)
        time.sleep(300)
    pressure = capture(['memory_pressure'])
    (state / 'memory.txt').write_text(pressure)
    free = re.search(r'memory free percentage:\s*(\d+)%', pressure)
    if not free or int(free[1]) < 30:
        raise RuntimeError('Need at least 30% free memory')


def quit_once(state):
    with (state / 'quit.log').open('w') as log:
        try:
            subprocess.run(['osascript', '-e', f'tell application "{APP}" to quit'],
                           stdout=log, stderr=subprocess.STDOUT, timeout=20)
        except subprocess.TimeoutExpired:
            log.write('Quit Apple event timed out; no force shutdown attempted.\n')


def screenshot(state):
    shot = state / 'blocked.png'
    subprocess.run(['screencapture', '-x', str(shot)], check=True)
    # Keep a center crop for dialog evidence; never retain the full desktop.
    subprocess.run(['sips', '--cropToHeightWidth', '900', '1400', str(shot)],
                   stdout=subprocess.DEVNULL, check=True)
    edge = 1000
    while True:
        subprocess.run(['sips', '-Z', str(edge), str(shot)],
                       stdout=subprocess.DEVNULL, check=True)
        if shot.stat().st_size <= 400_000:
            return
        edge = max(1, edge * 3 // 4)


def build(state, matrix="legacy", prevent_dialogs=True):
    out = state / 'build.json'
    if out.exists() or (state / 'launch.jsx').exists():
        raise RuntimeError('Build requires a fresh --run-id (no repeated dispatch)')
    if matrix == 'downsample-corpus':
        from corpus_inputs import prepare
        prepare(state / 'inputs')
    elif matrix != 'legacy':
        from downsample_inputs import prepare
        prepare(state / 'inputs', high_depth=matrix == 'downsample-depths')
        if matrix == 'downsample-straight':
            path = state / 'inputs/inputs.json'
            inputs = [r for r in json.loads(path.read_text()) if r['width'] == 1279]
            for row in inputs:
                row.update(plugin='ColorKeep', outputTemplate='_HIDDEN X-Factor 8',
                           outputExtension='png', requireStraight=True)
            path.write_text(json.dumps(inputs, indent=2) + '\n')
    else:
        with (state / 'inputs.log').open('w') as log:
            subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_inputs.py')),
                            str(state / 'inputs')], stdout=log, stderr=subprocess.STDOUT, check=True)
    specs = []
    for name in PLUGINS:
        pipl = (ROOT / f'mac/{name}/{name}PiPL.r').read_text()
        specs.append(dict(plugin=name, matchName=re.search(
            r'AE_Effect_Match_Name\s*\{\s*"([^"]+)"', pipl)[1]))
    config = dict(output=str(out), directory=str(state), plugins=specs,
                  inputs=json.loads((state / 'inputs/inputs.json').read_text()))
    config['matrix'] = matrix
    if matrix != 'legacy':
        import hashlib
        template = ROOT / 'refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep'
        expected = '51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679'
        if hashlib.sha256(template.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Preserve RGB input template hash mismatch')
        config['inputTemplate'] = str(template)
        config['inputTemplateSha256'] = expected
    wrapper = state / 'launch.jsx'
    wrapper.write_text('var A01=' + json.dumps(config) + ';\n$.evalFile(new File(' +
                       json.dumps(str(Path(__file__).with_name('prepare_downsample.jsx' if matrix != 'legacy' else 'prepare.jsx'))) + '));\n')
    preflight(state)
    wait_unlocked(state)
    # The user may have started AE while the screen was locked.
    preflight(state)
    if screen_locked():
        raise RuntimeError('Screen locked again after preflight; no AE launch')
    from ae_dialog_watch import DialogWatcher
    os.environ['OLM_AE_DIALOG_AUDIT_LOG'] = str(ROOT / 'orchestra/reports/A02b-evidence/dialogs.jsonl')
    watcher = DialogWatcher(state, prevention=prevent_dialogs).start()
    from ae_dialog_watch.prefs import scripting_prefs
    try:
        scripting_prefs(state / 'prefs')
        _build_owned(state, wrapper, out, watcher)
    finally:
        try:
            watcher.stop()
        finally:
            if (state / 'prefs/scripting-prefs.json').exists():
                scripting_prefs(state / 'prefs', restore=True)


def _build_owned(state, wrapper, out, watcher):
    # Compilation/prevention can take time: recheck just before dispatch.
    preflight(state)
    if screen_locked():
        raise RuntimeError('Screen locked before dispatch; no AE launch')
    watcher.check()
    dispatch = None
    dispatch_log = None
    proc = None
    try:
        with (state / 'ae.log').open('w') as log:
            proc = subprocess.Popen([str(APP / 'Contents/MacOS/After Effects')],
                                    stdout=log, stderr=subprocess.STDOUT)
            (state / 'pid.txt').write_text(str(proc.pid) + '\n')
            watcher.bind(proc.pid)
            deadline = time.monotonic() + 180
            result = None
            while time.monotonic() < deadline:
                watcher.check()
                if (watcher.directory / 'workspace-ready').exists() and dispatch is None:
                    if running() != [str(proc.pid)]:
                        raise RuntimeError('Owned AE is not the sole running instance')
                    dispatch_log = (state / 'dispatch.log').open('w')
                    script = 'tell application ' + json.dumps(str(APP)) + ' to DoScriptFile POSIX file ' + json.dumps(str(wrapper))
                    dispatch = subprocess.Popen(['osascript', '-e', script],
                                                stdout=dispatch_log, stderr=subprocess.STDOUT)
                    deadline = time.monotonic() + 180
                if out.exists():
                    try:
                        result = json.loads(out.read_text())
                        if result.get('phase') in ('complete', 'error'):
                            break
                    except json.JSONDecodeError:
                        pass
                if proc.poll() is not None:
                    break
                time.sleep(1)
            if not result or result.get('phase') not in ('complete', 'error'):
                raise RuntimeError(f'JSX did not finish within deadline; exit={proc.poll()}; stop, no retry')
            proc.wait(timeout=60)
            watcher.check()
            if running():
                raise RuntimeError('AE main executable still present after wrapper exit; stop')
            if result['phase'] != 'complete':
                raise RuntimeError('JSX failed: ' + result.get('error', 'unknown'))
    except BaseException:
        if proc is not None and proc.poll() is None:
            try:
                watcher.capture_owned(proc.pid)
            finally:
                quit_once(state)
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                pass
        raise
    finally:
        if dispatch is not None:
            dispatch.wait(timeout=30)
        if dispatch_log is not None:
            dispatch_log.close()


def render(state):
    data = json.loads((state / 'build.json').read_text())
    if data['phase'] != 'complete':
        raise RuntimeError('No complete build; rendering refused')
    if data['projects'] and 'outputPrefix' in data['projects'][0]['items'][0]:
        from render_downsample import render as render_matrix
        return render_matrix(state, data, APP, preflight)
    for row in data['projects']:
        preflight(state)
        with (state / f'aerender-{row["depth"]}.log').open('w') as log:
            subprocess.run([str(APP.parent / 'aerender'), '-project', row['path'],
                            '-mfr', 'OFF', '100'], stdout=log, stderr=subprocess.STDOUT, check=True)


def compare_controls(state):
    from decode import check_controls
    results = check_controls(state)
    (state / 'io-comparison.json').write_text(json.dumps(results, indent=2) + '\n')
    if not all(r['exact'] for r in results):
        raise RuntimeError('I/O controls differ; effect comparison cannot be interpreted')
    print('I/O controls exact; corpus and native-host matrix not implemented yet', flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=('prefs', 'build', 'render', 'compare', 'all'), default='all')
    p.add_argument('--restore', action='store_true', help='Restore the original scripting prefs (stage prefs only)')
    p.add_argument('--year', type=int, choices=(2026,), default=2026)
    p.add_argument('--run-id', default='run1')
    p.add_argument('--no-dialog-prevention', action='store_true',
                   help='Skip crash-flag backup/reset; watcher remains enabled')
    p.add_argument('--scratch', type=Path, help='Ticket-local scratch base')
    p.add_argument('--matrix', choices=('legacy', 'downsample-priority', 'downsample-depths', 'downsample-corpus', 'downsample-straight'), default='legacy')
    a = p.parse_args()
    if a.restore and a.stage != 'prefs':
        p.error('--restore requires --stage prefs')
    if a.matrix != 'legacy' and a.stage in ('compare', 'all'):
        p.error('downsample comparison is not implemented; use build or render explicitly')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', a.run_id):
        p.error('invalid run id')
    base = ROOT / 'orchestra/state/A02-real-ae-retest-downsample' if a.matrix != 'legacy' else STATE
    if a.scratch:
        base = a.scratch.resolve()
    state = base / a.run_id
    state.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(state), TMP=str(state), TEMP=str(state),
                      OLM_REFUSAL_TRACE=str(state / 'refusals.log'))
    if a.stage == 'prefs':
        from ae_dialog_watch.prefs import scripting_prefs
        print(json.dumps(scripting_prefs(state / 'prefs', restore=a.restore), indent=2))
        return
    for stage, action in [('build', build), ('render', render), ('compare', compare_controls)]:
        if a.stage in (stage, 'all'):
            print(stage, flush=True)
            if stage == 'build':
                build(state, a.matrix, prevent_dialogs=not a.no_dialog_prevention)
            else:
                action(state)


if __name__ == '__main__':
    main()
