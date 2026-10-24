#!/usr/bin/env python3
"""Verify synthetic expanded allocation, origins, byte stride and geometry forwarding."""
import os,subprocess
from pathlib import Path
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2]
def main():
 s=ROOT/'orchestra/state/F52c-geometry-hosts-and-campaigns/contract';s.mkdir(parents=True,exist_ok=True)
 env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s),OLM_F52_GEOMETRY_OUTPUT=str(s/'raw'),OLM_F52_DOWNSAMPLE='21,19,1,2,1,3',OLM_F52_ASPECT='10,11',OLM_F52_PADDING='3',OLM_F52_EXTENT='1,2,10,6',OLM_F52_REQUEST='-3,-2,14,10')
 subprocess.run(['clang++','-std=c++17','-O2','-Wno-pragma-pack','-I'+str(main_checkout()/'Headers'),'-I'+str(main_checkout()/'Headers/SP'),str(ROOT/'tools/fuzz/harnesses/geometry_contract.cpp'),'-o',str(s/'contract')],env=env,check=True)
 subprocess.run([s/'contract'],env=env,check=True)
 expected=b''.join(bytes([255,x-3+32,y-2+32,77]) for y in range(12) for x in range(17))
 assert (s/'raw').read_bytes()==expected
 print('PASS expanded 17x12, origin -3,-2, stride 71, 816 packed bytes; input metadata; output header restored')
if __name__=='__main__':main()
