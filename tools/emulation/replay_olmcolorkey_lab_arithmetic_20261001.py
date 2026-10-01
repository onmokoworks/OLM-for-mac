#!/usr/bin/env python3
"""Replay temporary Lab arithmetic against independent retained owner hashes."""
import argparse,json,os,tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
from colorkey_lab_arithmetic_candidate_20261001 import candidate_source

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path,required=True);ap.add_argument('--inputs',type=Path,nargs='+',required=True);args=ap.parse_args()
    source=owner.SOURCE.read_text();candidate=candidate_source(source);rows=[];counts={};env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1');original_fixture=owner.fixture
    with tempfile.TemporaryDirectory(prefix='olmck_lab_arithmetic_') as td:
        temp=Path(td)
        for sanitize,name in ((False,'o2'),(True,'asan_ubsan')):
            exe=owner.compile_public(temp/name,candidate,sanitize);n=0;exact=0
            for path in args.inputs:
                report=json.loads(path.read_text());cases=[c for c in report['cases'] if c.get('reference_status','measured')=='measured'];owner.fixture=independent.fixture if report['schema']=='olmcolorkey.lab-state-boundary/1' else original_fixture
                for c in cases:
                    raw,rb=owner.fixture(c['fixture'],c['depth']);assert owner.sha(raw)==c['input_sha256']
                    for route,rname in ((0,'classic'),(1,'smart')):
                        err,out=owner.mac_render(exe,temp,c,route,env if sanitize else None);match=err==0 and owner.sha(out)==c['actual_sha256'];n+=1;exact+=match
                        rows.append({'input_report':str(path.relative_to(owner.ROOT)) if path.is_absolute() else str(path),'label':c['label'],'depth':c['depth'],'threshold_bits':c.get('threshold_bits'),'build':name,'route':rname,'error':err,'actual_sha256':c['actual_sha256'],'candidate_sha256':owner.sha(out),'exact':match})
            counts[name]={'render_count':n,'exact_count':exact};print('LAB_ARITHMETIC',name,counts[name],flush=True)
    owner.fixture=original_fixture
    result={'schema':'olmcolorkey.lab-arithmetic-candidate-replay/1','summary':counts,'source_sha256':owner.sha(source.encode()),'candidate_source_sha256':owner.sha(candidate.encode()),'dependencies_sha256':{str(p.relative_to(owner.ROOT)):owner.sha(p.read_bytes()) for p in (Path(__file__),Path(owner.__file__),Path(independent.__file__),Path(__file__).with_name('colorkey_lab_arithmetic_candidate_20261001.py'),Path(__file__).with_name('colorkey_lab_mutation_candidate_20261001.py'),owner.HARNESS)},'input_report_sha256':{str(p.relative_to(owner.ROOT)) if p.is_absolute() else str(p):owner.sha(p.read_bytes()) for p in args.inputs},'cases':rows,'claims_not_made':['Temporary candidate; production source unchanged','No native Windows UCRT/AE/Mac installed conformance','No all-color/threshold/geometry or Lab94 scalar completion']}
    head=dict(result);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in rows)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==result
if __name__=='__main__':main()
