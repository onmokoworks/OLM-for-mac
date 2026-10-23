#!/usr/bin/env python3
"""Ensure empty/truncated streams cannot masquerade as numerical passes."""
import pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
b=root/'orchestra/state/F28-ucrtmath-lib-amd/build'
dll='/Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
raw=subprocess.check_output([str(b/'native'),'expf','sweep','1'])
for label,data,count,expected in [('valid',raw,1,0),('short',raw,2,2),('truncated',raw[:-1],1,2),('empty',b'',1,2)]:
 p=subprocess.run([str(b/'compare'),dll,'expf',str(count)],input=data,capture_output=True)
 assert p.returncode==expected,(label,p.returncode,p.stderr.decode())
 print('PASS',label,'exit',p.returncode)
