#!/usr/bin/env python3
"""Sequential seed-1 bundle/source campaigns; retain full reports for attribution."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS = dict(olmblur='OLMBlur', colorkeep='ColorKeep', olmcolorkey='OLMColorKey',
    olmdirectionalblur='OLMDirectionalBlur', olmdistancegradation='OLMDistanceGradation',
    olmkirakira='OLMKiraKira', olmsmoother2='OLMSmoother2', olmtoondilate='OLMToonDilate',
    radialblur='OLMRadialBlur', olmsmoother='OLMSmoother')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', type=Path, default=ROOT/'orchestra/state/F47d-native-plugin-all')
    p.add_argument('--plugins', nargs='+', choices=PLUGINS, default=list(PLUGINS))
    p.add_argument('--worker', type=Path)
    p.add_argument('--candidates', nargs='+', choices=('plugin-bundle', 'source'), default=['plugin-bundle', 'source'])
    p.add_argument('--n', type=int, default=100)
    args = p.parse_args()
    state = args.state.resolve()
    for plugin in args.plugins:
        for candidate in args.candidates:
            name = plugin+'-'+candidate
            command = [sys.executable, str(ROOT/'tools/fuzz/run.py'), '--plugin', plugin,
                '--candidate', candidate, '--worker', str((args.worker or state/'aex-guest-worker').resolve()),
                '--seed', '1', '--n', str(args.n), '--jobs', '1', '--case-timeout', '10',
                '--budget-minutes', '15', '--shrink-attempts', '0', '--shrink-seconds', '0',
                '--scratch', str(state/name), '--corpus', str(state/(name+'-corpus')),
                '--report', str(state/(name+'.json'))]
            if candidate == 'plugin-bundle':
                command += ['--plugin-bundle', str(state/'bundles/xcode'/PLUGINS[plugin]/'products'/(PLUGINS[plugin]+'.plugin'))]
            with (state/(name+'.log')).open('w') as log:
                result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            report_path = state/(name+'.json')
            report = json.loads(report_path.read_text()) if report_path.exists() else {}
            print(name, result.returncode, report.get('status'), report.get('summary'), flush=True)


if __name__ == '__main__':
    main()
