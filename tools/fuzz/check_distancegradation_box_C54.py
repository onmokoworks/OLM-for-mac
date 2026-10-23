#!/usr/bin/env python3
"""Compare reordered certified Box sums with the retained sequential operation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import sys
sys.dont_write_bytecode=True
from adapters.olmdistancegradation import SOURCE
from adapters.public import ROOT
from core import sha


def body(s, start):
    return s[s.index(start):s.index('// Legacy cvSmooth mode 3',s.index(start))]


def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--before-ref',default='8056458b0c71ba76130066c449c9eb9578faebfd');args=p.parse_args()
    args.scratch=args.scratch.resolve();assert args.scratch.is_relative_to(ROOT/'orchestra/state');args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch));tempfile.tempdir=str(args.scratch)
    old=subprocess.check_output(['git','show',args.before_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode()
    source=SOURCE.read_text()
    code='#include <algorithm>\n#include <cmath>\n#include <cstdint>\n#include <cstring>\n#include <cstdio>\n#include <vector>\n#include <random>\n'
    code+=body(old,'static void box_blur_separable').replace('box_blur_separable','original_box')
    code+=body(source,'static bool box_sum_is_exact')
    code+=r'''
int main() {
    std::mt19937 random(54); int cases=0, certified=0, fallback=0;
    for (int profile=0;profile<9;++profile) for (int kernel:{3,7,33,101})
    for (int w:{1,3,17}) for (int h:{1,5}) for (bool area:{false,true}) {
        std::vector<float> a(w*h);
        for (float &v:a) {
            const int n=(int)(random()%1025)-512;
            switch(profile) {
            case 0:v=(float)n;break;
            case 1:v=std::ldexp((float)n,-20);break;
            case 2:v=std::ldexp((float)n,(random()%100)-80);break;
            case 3:v=(float)(random()%65536)/65535.0f;break;
            case 4:v=(random()%2)?0.0f:-0.0f;break;
            case 5:v=std::ldexp((float)n,-149);break;
            case 6:v=std::ldexp((float)n,110);break;
            case 7:{uint32_t bits=(random()%2)?0x7f800000:0xff800000;memcpy(&v,&bits,4);break;}
            default:{uint32_t bits=0x7fc12345;memcpy(&v,&bits,4);}
            }
        }
        auto b=a;bool fast=box_sum_is_exact(a.data(),a.size(),kernel);
        fast?++certified:++fallback;
        original_box(a.data(),w,h,kernel,area);
        box_blur_separable(b.data(),w,h,kernel,area,true);
        if(memcmp(a.data(),b.data(),a.size()*4)) {fprintf(stderr,"difference profile%d kernel%d %dx%d area%d certified%d\n",profile,kernel,w,h,area,fast);return 1;}
        ++cases;
    }
    printf("cases=%d certified=%d fallback=%d differing=0\n",cases,certified,fallback);
}
'''
    report=dict(source_sha256=sha(source.encode()),before_ref=args.before_ref,builds=[])
    with tempfile.TemporaryDirectory(dir=args.scratch) as d:
        d=Path(d);cpp=d/'probe.cpp';cpp.write_text(code)
        for name,flags in [('O2',[]),('san',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            binary=d/name
            subprocess.run(['clang++','-std=c++17','-O2','-ffp-contract=off',*flags,str(cpp),'-o',str(binary)],check=True)
            r=subprocess.run([str(binary)],check=False,capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1'))
            assert r.returncode == 0 and not r.stderr, (r.returncode,r.stdout,r.stderr)
            report['builds'].append(dict(name=name,output=r.stdout.strip()));print(name,r.stdout.strip())
    args.report.write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
