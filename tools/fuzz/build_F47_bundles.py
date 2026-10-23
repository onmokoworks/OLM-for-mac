#!/usr/bin/env python3
"""Build F47 Universal Release bundles without modifying the source projects."""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'orchestra/state/F47-aexcompat-native-plugin-host'

def main():
    global SCRATCH
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, default=SCRATCH)
    parser.add_argument('--plugins', nargs='+', choices=('OLMBlur', 'OLMColorKey', 'OLMRadialBlur'),
                        default=['OLMBlur', 'OLMColorKey', 'OLMRadialBlur'])
    args = parser.parse_args()
    SCRATCH = args.scratch.resolve()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH))
    subprocess.run([str(ROOT / 'scripts/setup_ae_sdk_links.sh')], env=env, check=True)
    records = []
    for name in args.plugins:
        source = ROOT / 'mac' / name / 'Mac'
        build = SCRATCH / 'xcode' / name
        project = build / f'{name}.xcodeproj'
        project.mkdir(parents=True, exist_ok=True)
        # These projects only define Debug. Rename the configuration in a disposable
        # project, retaining all production source references and compiler options.
        original = (source / f'{name}.xcodeproj/project.pbxproj').read_text()
        original = re.sub(r'path = (\.\./[^;]+);',
                          lambda m: 'path = ' + json.dumps(str((source / m[1]).resolve())) + ';', original)
        original = re.sub(r'(?m)^(\s*)(\.\./[^,\n]+),$',
                          lambda m: m[1] + json.dumps('"' + str((source / m[2]).resolve()) + '"') + ',', original)
        (project / 'project.pbxproj').write_text(original.replace('Debug', 'Release'))
        cmd = ['xcodebuild', '-project', str(project), '-configuration', 'Release',
               '-jobs', '1', f'SRCROOT={source}', f'INFOPLIST_FILE={source}/{name}.plugin-Info.plist', 'ARCHS=arm64 x86_64',
               'ONLY_ACTIVE_ARCH=NO', 'MACOSX_DEPLOYMENT_TARGET=11.0',
               f'OBJROOT={build}/obj', f'SYMROOT={build}/products',
               f'SHARED_PRECOMPS_DIR={build}/pch',
               f'CONFIGURATION_BUILD_DIR={build}/products',
               'GCC_OPTIMIZATION_LEVEL=2', 'ENABLE_TESTABILITY=NO',
               'CODE_SIGNING_ALLOWED=NO', 'build']
        with (SCRATCH / f'build-{name}.log').open('w') as log:
            subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        executable = build / f'products/{name}.plugin/Contents/MacOS/{name}'
        archs = subprocess.check_output(['lipo', '-archs', str(executable)], text=True).strip()
        records.append(dict(plugin=name, command=cmd, architectures=archs))
        for directory in ('obj', 'pch'):
            shutil.rmtree(build / directory, ignore_errors=True)
        print(name, archs, flush=True)
    (SCRATCH / 'bundle-builds.json').write_text(json.dumps(records, indent=2) + '\n')

if __name__ == '__main__':
    main()
