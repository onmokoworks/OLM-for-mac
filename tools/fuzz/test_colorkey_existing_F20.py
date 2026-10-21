#!/usr/bin/env python3
"""Run existing fast ColorKey tests with read-only MAIN SDK paths in a worktree."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT.parent.parent
SCRATCH = ROOT/'orchestra/state/F20-colorkey-zero-color-and-byte-safe/tests'


def main():
    SCRATCH.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH),
                      ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1')
    tempfile.tempdir = str(SCRATCH)
    original_run = subprocess.run

    def run(argv,*args,**kwargs):
        # Tests historically assume the SDK is in their checkout. Resolve only
        # those external SDK inputs; production source remains in this worktree.
        if isinstance(argv,list) and argv and argv[0]=='clang++':
            argv = [('-I'+str(MAIN/str(a)[2:])) if str(a) in
                    ('-IHeaders','-IHeaders/SP','-IUtil','-IResources') else
                    str(MAIN/a) if str(a) in ('Util/AEGP_SuiteHandler.cpp','Util/MissingSuiteError.cpp')
                    else a for a in argv]
        return original_run(argv,*args,**kwargs)

    subprocess.run = run
    selected = {
        'test_olmcolorkey_parameter_ui_parity_20260806': None,
        'test_olmcolorkey_generic_pixel_local_beta': None,
        'test_olmcolorkey_generic_pixel_local_pairwise':
            {'test_generic_pixel_local_pairwise_matrix','test_generic_edge_thin_under_asan_ubsan'},
    }
    suite = unittest.TestSuite()
    for name, names in selected.items():
        spec = importlib.util.spec_from_file_location(name,ROOT/'tests'/(name+'.py'))
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for key,value in vars(module).items():
            if key.startswith('test_') and callable(value) and (names is None or key in names):
                suite.addTest(unittest.FunctionTestCase(value,description=name+'.'+key))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()


if __name__=='__main__': main()
