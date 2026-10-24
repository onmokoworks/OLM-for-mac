#!/usr/bin/env python3
"""Verify successful empty negotiated output through the complete bundle transport."""
import os,subprocess
from pathlib import Path
from run import main_checkout
from adapters.bundle_geometry import HOST
from adapters.public import geometry_environment
from measure_F52c import ROOT,S

def main():
 s=S/'empty-bundle';s.mkdir(parents=True,exist_ok=True)
 env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s))
 main=main_checkout();binary=s/'empty.dylib'
 subprocess.run(['clang++','-std=c++17','-dynamiclib','-Wno-pragma-pack','-I'+str(main/'Headers'),'-I'+str(main/'Headers/SP'),str(ROOT/'tools/fuzz/harnesses/geometry_empty_bundle.cpp'),'-o',str(binary)],check=True,env=env)
 (s/'decl').write_text('1\n0\n');(s/'params').write_text('')
 geometry_environment(dict(geometry_sampler='realistic-v1',full_geometry=[21,19],downsample=[[1,2],[1,3]],extent_hint=[0,0,11,7],request_rect=[0,0,11,7],pixel_aspect=[10,11],rowbytes_padding=3),s,env)
 r=subprocess.run([HOST,binary,'11','7','8','3','1',s/'decl',s/'params'],input=bytes(11*7*4),capture_output=True,env=env)
 (s/'stderr.log').write_bytes(r.stderr)
 assert r.returncode==0 and r.stdout==bytes(4),(r.returncode,r.stdout,r.stderr.decode())
 assert b'GEOMETRY 0 0 0 0\n' in r.stderr
 assert (s/'geometry-output.raw').read_bytes()==b''
 print('PASS empty bundle output: success return, empty pixels, SmartRender skipped')
if __name__=='__main__':main()
