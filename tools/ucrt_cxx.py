#!/usr/bin/env python3
"""C++ harness linker wrapper. Set CXX to this path, or expose it as clang++.

Builds independent C objects beside the requested output; preserves all C++
flags. --compiler NAME preserves an explicit compiler selection; --xcrun
retains xcrun's SDK environment. OLM_UCRT_LINK_LOG optionally records command
exit codes as JSONL for audits. SDK paths and architecture selection remain the caller's responsibility.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]/'ucrtmath'
args=sys.argv[1:]
compiler=os.environ.get('UCRT_CXX','/usr/bin/clang++')
if args[:1] == ['--compiler']:
    compiler, args = args[1], args[2:]
use_xcrun = args[:1] == ['--xcrun']
if use_xcrun:
    args = args[1:]
if '-o' in args and not any(flag in args for flag in ('-c', '-S', '-E', '-fsyntax-only')):
    output=Path(args[args.index('-o')+1]).resolve()
    library=output.parent/(output.name+'-ucrtmath')
    architectures = list(dict.fromkeys(args[i+1] for i,a in enumerate(args[:-1]) if a == '-arch')) or ['arm64']
    archives = []
    for arch in architectures:
        directory = library/arch
        subprocess.run(['sh',str(ROOT/'build.sh'),str(directory),arch],check=True)
        archives.append(str(directory/'libucrtmath.a'))
    if len(archives) == 1:
        args.append(archives[0])
    else:
        combined = str(library/'libucrtmath.a')
        subprocess.run(['lipo','-create',*archives,'-output',combined],check=True)
        args.append(combined)
command = ['xcrun', 'clang++', *args] if use_xcrun else [compiler, *args]
if os.environ.get('OLM_UCRT_LINK_LOG'):
    result = subprocess.run(command)
    with open(os.environ['OLM_UCRT_LINK_LOG'], 'a') as log:
        log.write(json.dumps({'command': command, 'exit': result.returncode}) + '\n')
    sys.exit(result.returncode)
os.execvp(command[0], command)
