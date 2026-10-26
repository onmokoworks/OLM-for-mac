#!/usr/bin/env python3
"""Run the all-plugin HEAD identity matrix, retaining compact evidence."""
import json
from pathlib import Path
import subprocess
import sys
import native_diff
from native_diff import PLUGINS, ROOT


def main():
    scratch = ROOT/'orchestra/state/Q00-refactor-native-diff-tool/self-test'
    scratch.mkdir(parents=True, exist_ok=True)
    results = {}
    for plugin in PLUGINS:
        command = [sys.executable, str(ROOT/'tools/refactor/native_diff.py'),
                   '--plugin', plugin, '--base', 'HEAD', '--head', 'HEAD',
                   '--cases', '18', '--seed', '909', '--arch', 'both', '--build', 'both',
                   '--jobs', '1', '--scratch', str(scratch)]
        with (scratch/(plugin+'.log')).open('w') as log:
            proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        summary = json.loads((scratch/plugin/'summary.json').read_text())
        results[plugin] = dict(exit=proc.returncode, counts=summary['counts'],
                               coverage=summary['coverage'], builds=summary['builds'],
                               base=summary.get('base'), fatal_error=summary.get('fatal_error'))
        (scratch/'results.json').write_text(json.dumps(results, indent=2)+'\n')
        print(plugin, proc.returncode, summary['counts'], flush=True)
    return int(any(r['exit'] for r in results.values()))


def mutation():
    """Plant one float ULP only in the archived head copy, then run the real CLI."""
    snapshot = native_diff.snapshot

    def planted_snapshot(revision, destination):
        sha = snapshot(revision, destination)
        if destination.name == 'head-source':
            source = destination/'mac/ColorKeep/ColorKeep.cpp'
            body = source.read_text()
            anchor = 'if (!match) pixel.alpha = 0.0f;'
            assert body.count(anchor) == 1
            source.write_text('#include <cmath>\n' + body.replace(anchor, anchor +
                '\n\tif (std::isfinite(pixel.red)) pixel.red = std::nextafter(pixel.red, INFINITY);'))
        return sha

    native_diff.snapshot = planted_snapshot
    scratch = ROOT/'orchestra/state/Q00-refactor-native-diff-tool/mutation'
    sys.argv = [str(ROOT/'tools/refactor/native_diff.py'), '--plugin', 'colorkeep',
                '--base', 'HEAD', '--head', 'HEAD', '--cases', '3', '--seed', '909',
                '--arch', 'both', '--build', 'both', '--scratch', str(scratch)]
    try:
        code = native_diff.main()
    finally:
        native_diff.snapshot = snapshot
    summary = json.loads((scratch/'colorkeep/summary.json').read_text())
    assert code == 1 and summary['counts']['difference'] > 0, summary
    assert summary['counts']['execution_errors'] == 0, summary
    assert all(d['case']['depth'] == 32 and d['first_byte_difference'] is not None
               for d in summary['differences'])
    assert not (scratch/'colorkeep/run').exists(), 'planted copy was not removed'
    return 0


if __name__ == '__main__':
    sys.exit(mutation() if sys.argv[1:] == ['--mutation'] else main())
