#!/usr/bin/env python3
"""Replay the retained six Smart fixtures with both optional callback variants.

Use the original positive controls, including padding/copy/lifecycle assertions.
Negative admissions intentionally expanded by F17 are tested by the new matrix.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile
import time
from adapters.olmblur import Adapter, HOST, SOURCE, CORES
from core import command, sha
from run import ROOT, main_checkout
from verify_blur_small_F17 import WORKER


def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/F17-fuzz-per-route-oracle')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    class Sanitized(Adapter):
        def compile(self,argv,deadline):
            if argv[0]=='clang++':argv=[*argv[:1],'-fsanitize=address,undefined','-fno-sanitize-recover=all',*argv[1:]]
            return super().compile(argv,deadline)
    a=Sanitized(argparse.Namespace(max_size=256,case_timeout=20,main=main_checkout(),worker=WORKER))
    a.env.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch),
                 ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    body=HOST.read_text().replace('../../mac/OLMBlur/OLMBlur.cpp',str(SOURCE))
    body=body.split('  const NegSpec negatives[]={',1)[0]+'  return ok ? 0 : 4;\n}\n'
    fixture=ROOT/'tools/emulation/fixtures/olmblur_amount_repeat_legacy_matrix_20260810'
    with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        binary=a.compile_sdk(Path(td),body,SOURCE,time.monotonic()+120,CORES)
        status,out,err=command([binary,fixture],timeout=60,deadline=time.monotonic()+60,env=a.env)
        report={'source_sha256':sha(SOURCE.read_bytes()),'candidate_sha256':sha(binary.read_bytes()),
                'original_host_sha256':sha(HOST.read_bytes()),'fixture_manifest_sha256':sha((fixture/'manifest.json').read_bytes()),
                'status':status,'lines':out.decode().splitlines(),'stderr':err.decode()}
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    assert status['status']=='ok' and len(report['lines'])==12 and all('pass=1' in line for line in report['lines']),report
    print('PASS 12 retained positive controls; active bytes, padding, guards and callbacks preserved')


if __name__=='__main__':main()
