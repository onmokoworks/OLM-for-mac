#!/usr/bin/env python3
"""C++ harness linker wrapper. Set CXX to this path, or expose it as clang++.

Builds independent C objects beside the requested output; preserves all C++
flags. SDK paths and architecture selection remain the caller's responsibility.
"""
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]/'ucrtmath'
args=sys.argv[1:]
compiler=os.environ.get('UCRT_CXX','/usr/bin/clang++')
if '-o' in args and '-c' not in args:
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
os.execv(compiler,[compiler,*args])
