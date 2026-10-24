#!/usr/bin/env python3
"""Refresh only the PF16 retained-owner runner identities after exact replays."""
import argparse, hashlib, importlib, json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R07-gate-contracts-and-bindings/blur-owner';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='2',PYTHONDONTWRITEBYTECODE='1');tempfile.tempdir=str(S)
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation')]
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
m=importlib.import_module('test_olmblur_pf16_retained_tuples_exported_public_owner_20260813')
old=json.loads(m.REPORT.read_text());a=m.live();b=m.live()
assert a==b,'original owner repetitions differ'
assert {k:v for k,v in old.items() if k!='identities'}=={k:v for k,v in a.items() if k!='identities'},'non-identity change'
assert old['identities']['aex']==a['identities']['aex']
assert m.DOC.read_text()==m.markdown(a),'documentation changed'
fixtures=S/'fixtures';fixtures.mkdir(exist_ok=True);records=[]
for case in m.worker.CASES:
 source=m.worker.source_bytes(case['width'],case['height'])
 first,meta=m.worker.run_case(case);second,meta2=m.worker.run_case(case)
 assert first==second and meta==meta2
 target=fixtures/case['id'];target.mkdir(exist_ok=True)
 (target/'source_argb16.bin').write_bytes(source);(target/'expected_argb16.bin').write_bytes(first)
 records.append(dict(id=case['id'],bytes=len(first),sha256=hashlib.sha256(first).hexdigest(),repetitions=2,instructions=meta['instructions']))
with tempfile.TemporaryDirectory(dir=S,prefix='build-') as tmp:
 exe=Path(tmp)/'replay'
 command=[str(ROOT/'tools/ucrt_cxx.py'),'-std=c++17','-O2','-ffp-contract=off','-fno-fast-math','-Icore','core/olmblur_helper.cpp','core/olmblur_worker16_nonlegacy.cpp','tools/emulation/replay_olmblur_worker16_nonlegacy.cpp','-o',str(exe)]
 subprocess.run(command,cwd=ROOT,check=True)
 subprocess.run([str(exe),str(fixtures)],cwd=ROOT,check=True)
(S/'result.json').write_text(json.dumps(dict(applied=args.apply,records=records,twice_identical_public_owner=True,non_identity_fields_unchanged=True,before=old['identities'],after=a['identities']),indent=2)+'\n')
text=m.REPORT.read_text()
for key in ['public_runner','worker_runner']:
 assert old['identities'][key]['path']==a['identities'][key]['path']
 text=text.replace(old['identities'][key]['sha256'],a['identities'][key]['sha256'])
assert json.loads(text)==a
if args.apply: m.REPORT.write_text(text)
print('Two original owner repeats and two worker repeats per case; current Mac worker exact; applied',args.apply)
# The separate 7x5 owner has the same metadata-only drift.
n=importlib.import_module('test_olmblur_pf16_7x5_exported_public_owner_20260813')
old7=json.loads(n.REPORT.read_text());a7=n.live();b7=n.live()
assert a7==b7
assert {k:v for k,v in old7.items() if k!='identities'}=={k:v for k,v in a7.items() if k!='identities'}
assert n.DOC.read_text()==n.md(a7)
source=n.source_bytes(7,5,'border');case=dict(kind='border',width=7,height=5,blur_amount=4.0,repeat=1,bias_direction=1)
expected,instructions=n.run_actual(case,source);again,instructions2=n.run_actual(case,source)
assert expected==again and instructions==instructions2
cpp=r'''
#include "olmblur_worker16_nonlegacy.h"
#include <fstream>
#include <iterator>
#include <vector>
int main(int argc,char**argv){if(argc!=3)return 2;
std::ifstream in(argv[1],std::ios::binary);std::vector<unsigned char> source((std::istreambuf_iterator<char>(in)),{});
if(source.size()!=7*5*8)return 3;std::vector<unsigned char> output(source.size());
const olm::blur::worker16::Params params{4.0f,100.0f,1,1};
olm::blur::worker16::render_nonlegacy(source.data(),output.data(),7,5,params);
std::ofstream out(argv[2],std::ios::binary);out.write(reinterpret_cast<const char*>(output.data()),output.size());return out?0:4;}
'''
with tempfile.TemporaryDirectory(dir=S,prefix='build-7x5-') as tmp:
 d=Path(tmp);(d/'probe.cpp').write_text(cpp);(d/'input.bin').write_bytes(source)
 subprocess.run([str(ROOT/'tools/ucrt_cxx.py'),'-std=c++17','-O2','-ffp-contract=off','-fno-fast-math','-Icore','core/olmblur_helper.cpp','core/olmblur_worker16_nonlegacy.cpp',str(d/'probe.cpp'),'-o',str(d/'replay')],cwd=ROOT,check=True)
 subprocess.run([str(d/'replay'),str(d/'input.bin'),str(d/'output.bin')],check=True)
 observed=(d/'output.bin').read_bytes();assert observed==expected
text=n.REPORT.read_text()
for key in a7['identities']:
 assert old7['identities'][key]['path']==a7['identities'][key]['path']
 text=text.replace(old7['identities'][key]['sha256'],a7['identities'][key]['sha256'])
assert json.loads(text)==a7
if args.apply:n.REPORT.write_text(text)
(S/'result-7x5.json').write_text(json.dumps(dict(applied=args.apply,bytes=len(expected),sha256=hashlib.sha256(expected).hexdigest(),instructions=instructions,original_owner_repetitions=2,original_worker_repetitions=2,mac_exact=True,first_mismatch=None,before=old7['identities'],after=a7['identities']),indent=2)+'\n')
print('7x5: twice-identical original owner and worker; current Mac exact, 280 bytes; applied',args.apply)
# Legacy owner retains its explicit worker-vs-public mismatch; never promote it.
l=importlib.import_module('test_olmblur_pf16_legacy_retained_exported_public_owner_20260813')
oldl=json.loads(l.REPORT.read_text());al=l.live();bl=l.live();assert al==bl
assert {k:v for k,v in oldl.items() if k!='identities'}=={k:v for k,v in al.items() if k!='identities'}
assert l.DOC.read_text()==l.markdown(al)
legacy=S/'legacy-fixtures';legacy.mkdir(exist_ok=True);records=[]
for case in l.worker.CASES:
 source=l.worker.source_bytes(case['width'],case['height'],case.get('mixed_alpha',False),case.get('pattern',''))
 first,meta=l.worker.run_case(case);second,meta2=l.worker.run_case(case)
 assert first==second and meta==meta2
 target=legacy/case['id'];target.mkdir(exist_ok=True)
 (target/'source_argb16.bin').write_bytes(source);(target/'expected_argb16.bin').write_bytes(first)
 records.append(dict(id=case['id'],bytes=len(first),sha256=hashlib.sha256(first).hexdigest(),repetitions=2,instructions=meta['instructions']))
with tempfile.TemporaryDirectory(dir=S,prefix='build-legacy-') as tmp:
 exe=Path(tmp)/'replay'
 subprocess.run([str(ROOT/'tools/ucrt_cxx.py'),'-std=c++17','-O2','-ffp-contract=off','-fno-fast-math','-Icore','core/olmblur_helper.cpp','core/olmblur_worker16_legacy.cpp','core/olmblur_fullworker_helper.cpp','tools/emulation/replay_olmblur_worker16_legacy.cpp','-o',str(exe)],cwd=ROOT,check=True)
 subprocess.run([str(exe),str(legacy)],cwd=ROOT,check=True)
text=l.REPORT.read_text()
for key in al['identities']:
 assert oldl['identities'][key]['path']==al['identities'][key]['path']
 text=text.replace(oldl['identities'][key]['sha256'],al['identities'][key]['sha256'])
assert json.loads(text)==al
canonical=hashlib.sha256(json.dumps(al,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
generator=Path(l.__file__);generated=generator.read_text().replace(l.EXPECTED_CANONICAL_SHA256,canonical)
testpath=ROOT/'tests/test_olmblur_pf16_legacy_retained_exported_public_owner_20260813.py'
import re
test=testpath.read_text()
test,count1=re.subn(r'(self.assertEqual\(sha\(GENERATOR\), ")[a-f0-9]{64}',lambda x:x[1]+hashlib.sha256(generated.encode()).hexdigest(),test)
test,count2=re.subn(r'(self.assertEqual\(sha\(MODULE.REPORT\), ")[a-f0-9]{64}',lambda x:x[1]+hashlib.sha256(text.encode()).hexdigest(),test)
assert count1==count2==1
if args.apply:
 l.REPORT.write_text(text);generator.write_text(generated);testpath.write_text(test)
(S/'result-legacy.json').write_text(json.dumps(dict(applied=args.apply,records=records,original_owner_repetitions=2,non_identity_fields_unchanged=True,retained_public_mismatch_bytes=369,canonical_sha256=canonical,before=oldl['identities'],after=al['identities']),indent=2)+'\n')
print('Legacy: twice-identical original owner/worker, 4 current Mac worker cases exact; retained public-worker mismatch369 unchanged; applied',args.apply)
