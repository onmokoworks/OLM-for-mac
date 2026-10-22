#!/usr/bin/env python3
"""Reproduce the rejected PF32 Legacy expf candidate without source edits."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
sys.dont_write_bytecode=True
from adapters import olmblur
from core import sha, raw_diff
from run import ROOT
from verify_blur_retained_C12 import verify


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();s=args.scratch.resolve()
    assert s.is_relative_to(ROOT/'orchestra/state/C15-olmblur-smart-r4')
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    original=olmblur.CORES
    compile_sdk=olmblur.Adapter.compile_sdk
    def observed_compile(self,scratch,body,source,deadline,*args,**kwargs):
        anchor='bool success=m==OK32&&c.output?'
        assert body.count(anchor)==1
        observer='if(strcmp(c.id,"legacy_24x24_smooth37_5")==0){FILE*f=fopen(getenv("C15_BLUR_OUTPUT"),"wb");if(f){for(int y=0;y<c.h;++y)fwrite(op+(size_t)y*rb,1,c.w*16,f);fclose(f);}}'
        return compile_sdk(self,scratch,body.replace(anchor,observer+anchor),source,deadline,*args,**kwargs)
    olmblur.Adapter.compile_sdk=observed_compile
    with tempfile.TemporaryDirectory(prefix='expf_',dir=s) as td:
        path=ROOT/'core/olmblur_worker32_legacy.cpp';body=path.read_text()
        anchor='static_cast<float>(std::exp(static_cast<double>(exponent)))'
        assert body.count(anchor)==1
        candidate=Path(td)/path.name;candidate.write_text(body.replace(anchor,'std::exp(exponent)'))
        os.environ["C15_BLUR_OUTPUT"]=str(Path(td)/"before.bin")
        before=verify(s)
        try:
            olmblur.CORES=[candidate if x==path else x for x in original]
            os.environ["C15_BLUR_OUTPUT"]=str(Path(td)/"after.bin")
            after=verify(s)
        finally:
            olmblur.CORES=original
            olmblur.Adapter.compile_sdk=compile_sdk
            os.environ.pop("C15_BLUR_OUTPUT",None)
        b=(Path(td)/"before.bin").read_bytes();a=(Path(td)/"after.bin").read_bytes()
        report=dict(fixture='legacy_24x24_smooth37_5',baseline_sha256=sha(b),experiment_sha256=sha(a),diff=raw_diff(b,a,32),source_sha256=sha(path.read_bytes()),candidate_source_sha256=sha(candidate.read_bytes()),before=before,after=after)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    bad=[x for x in after['lines'] if 'exact=1' not in x]
    print('before',before['status'],'after',after['status'],'bad',bad,'diff',report['diff'])
    assert before['status']['status']=='ok' and len(before['lines'])==80
    assert after['status']['status']=='error' and len(bad)==2
    assert all('legacy_24x24_smooth37_5' in x for x in bad)

if __name__=='__main__':main()
