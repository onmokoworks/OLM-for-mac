#!/usr/bin/env python3
"""Run the unchanged fuzz runner with a historical ColorKey source in scratch.

Only source selection changes: no checkout, MAIN write, generator or oracle
change. All other arguments are run.py arguments; sanitizers use T12's flags.
"""
import subprocess
import sys

import run
from adapters import olmcolorkey
from core import sha


def main():
    index = sys.argv.index('--source-ref')
    revision = sys.argv[index+1]
    del sys.argv[index:index+2]
    assert sys.argv[sys.argv.index('--plugin')+1]=='olmcolorkey'
    relative = 'mac/OLMColorKey/OLMColorKey.cpp'
    source = subprocess.check_output(['git','show',revision+':'+relative],cwd=run.ROOT).decode()
    original_compile = olmcolorkey.Adapter.compile_sdk
    original_prepare = olmcolorkey.Adapter.prepare

    def compile_sdk(self,scratch,body,path,deadline,cores=()):
        historical = scratch/'historical-OLMColorKey.cpp'
        historical.write_text(source.replace('#include "OLMColorKey.h"',
            '#include "'+str(olmcolorkey.SOURCE.with_suffix('.h'))+'"'))
        body = body.replace(str(olmcolorkey.SOURCE),str(historical))
        return original_compile(self,scratch,body,path,deadline,cores)

    def prepare(self,scratch,deadline):
        provenance = original_prepare(self,scratch,deadline)
        provenance['dependencies_sha256'][relative] = sha(source.encode())
        provenance['historical_colorkey_revision'] = revision
        return provenance

    olmcolorkey.Adapter.compile_sdk = compile_sdk
    olmcolorkey.Adapter.prepare = prepare
    return run.main()


if __name__=='__main__': raise SystemExit(main())
