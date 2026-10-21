#!/usr/bin/env python3
"""C03 diagnostic campaign wrapper; gate changes exist only in scratch sources."""
import argparse
import os
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from adapters.olmdistancegradation import Adapter, SOURCE, SHIM_DIR, FIELDGEN
from adapters.public import ROOT, replace_once
from core import sha
import run


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--experiment', choices=['none', 'domain', 'profile', 'all'], default='none')
    parser.add_argument('--sanitized', action='store_true')
    parser.add_argument('--source', type=Path)
    parser.add_argument('--smart-only', action='store_true')
    args, rest = parser.parse_known_args()
    original_build = Adapter.build
    def build(self, scratch, deadline):
        binary, deps = original_build(self, scratch, deadline)
        source = (args.source or SOURCE).read_text()
        if args.experiment in ('domain', 'all'):
            source = replace_once(source, '!pf32_smart_worlds_are_bounded_sdr(input, output)',
                                  'false /* C03 diagnostic: domain gate disabled */')
        if args.experiment in ('profile', 'all'):
            source = replace_once(source, 'if (!p.pf32_smart_matrix_admitted && !unblurred_beta && !blurred_beta &&',
                                  'if (false && !p.pf32_smart_matrix_admitted && !unblurred_beta && !blurred_beta &&')
        source = source.replace('#include "OLMDistanceGradation.h"', '#include "'+str(SOURCE.with_suffix('.h'))+'"')
        source = source.replace('"../../core/', '"'+str(ROOT/'core')+'/')
        cpp = scratch/'candidate.cpp'; cpp.write_text(source)
        host = scratch/'host.cpp'
        host.write_text(replace_once(host.read_text(), str(SOURCE), str(cpp)))
        flags = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all'] if args.sanitized else []
        self.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',*flags,
                      '-I',SHIM_DIR,host,FIELDGEN,'-o',binary],deadline)
        self.env.update(ASAN_OPTIONS='detect_leaks=0', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        self.c03 = dict(experiment=args.experiment,sanitized=args.sanitized,
                        source_sha256=sha((args.source or SOURCE).read_bytes()),
                        generated_source_sha256=sha(cpp.read_bytes()))
        return binary,deps
    original_scope=Adapter.scope
    Adapter.build=build
    Adapter.scope=lambda self: dict(original_scope(self), C03=self.c03)
    if args.smart_only: Adapter.routes=('smart',)
    sys.argv=[sys.argv[0],*rest]
    run.main()

if __name__=='__main__': main()
