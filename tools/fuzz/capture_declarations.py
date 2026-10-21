#!/usr/bin/env python3
"""Refresh a hash-bound original PARAMS_SETUP snapshot; no frames are rendered.

Use only after reviewing builder drift, never silently refresh campaign bindings.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.dont_write_bytecode = True
from adapters.public import messages
from core import command, sha
from run import ROOT, default_worker, main_checkout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plugin',required=True,help='Adapter module name')
    parser.add_argument('--aex-name',required=True,help='Original basename, e.g. OLMDirectionalBlur')
    parser.add_argument('--worker',type=Path,default=default_worker())
    parser.add_argument('--main',type=Path,default=main_checkout())
    parser.add_argument('--scratch',type=Path,required=True)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    if not scratch.is_relative_to(ROOT/'orchestra/state') or not args.plugin.isidentifier():
        parser.error('scratch must be in worktree/orchestra/state and plugin must be a module name')
    scratch.mkdir(parents=True,exist_ok=True)
    aex = args.main/'plugins_2025'/f'{args.aex_name}.aex'
    with tempfile.TemporaryDirectory(dir=scratch) as td:
        p = Path(td);(p/'input').write_bytes(bytes(4))
        status,out,err = command([args.worker,'session',aex,p/'input',p/'output','1','1','24',
            '--pixel-format','argb8'],data=b'',timeout=20,deadline=time.monotonic()+20,
            env=dict(os.environ,TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch)))
        if status['status']!='ok':
            raise RuntimeError(repr(status)+' '+err.decode(errors='replace')[-1000:])
        setup = next(m['setup'] for m in messages(out) if m['type']=='session_ready')
        assert not setup['global_setup_error'] and not setup['params_setup_error']
        data = {'aex_sha256':sha(aex.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),
                'parameters':setup['parameters'],
                'capture':'Original AEX PARAMS_SETUP via existing AEXCompat session protocol, no render'}
        path = ROOT/f'tools/fuzz/declarations/{args.plugin}.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
        print(args.plugin,len(setup['parameters']),'parameters',data['aex_sha256'])


if __name__=='__main__':
    main()
