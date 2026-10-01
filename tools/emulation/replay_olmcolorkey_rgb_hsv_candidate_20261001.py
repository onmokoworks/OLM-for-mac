#!/usr/bin/env python3
"""Replay RGB/HSV restoration against retained typed HDR/palette owner hashes."""
import argparse,json,os,tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_color_hdr_palette_20261001 as campaign
from colorkey_rgb_hsv_candidate_20261001 import candidate_source
BASE=owner.ROOT/'reports/colorkey_color_hdr_palette_baseline_20261001.json'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();base=json.loads(BASE.read_text());source=owner.SOURCE.read_text();candidate=candidate_source(source);owner.fixture=campaign.fixture;rows=[];counts={};env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
    with tempfile.TemporaryDirectory(prefix='olmck_rgb_hsv_candidate_') as td:
        temp=Path(td)
        for sanitize,name in ((False,'o2'),(True,'asan_ubsan')):
            exe=owner.compile_public(temp/name,candidate,sanitize);n=0;exact=0
            for c in base['cases']:
                raw,_=campaign.fixture(c['fixture'],c['depth']);assert owner.sha(raw)==c['input_sha256']
                for route,rname in ((0,'classic'),(1,'smart')):
                    err,out=owner.mac_render(exe,temp,c,route,env if sanitize else None);match=err==0 and owner.sha(out)==c['actual_sha256'];n+=1;exact+=match;rows.append({'label':c['label'],'depth':c['depth'],'build':name,'route':rname,'error':err,'actual_sha256':c['actual_sha256'],'candidate_sha256':owner.sha(out),'exact':match})
            counts[name]={'render_count':n,'exact_count':exact};print('RGB_HSV_CANDIDATE',name,counts[name],flush=True)
    r={'schema':'olmcolorkey.rgb-hsv-candidate-replay/1','summary':counts,'source_sha256':owner.sha(source.encode()),'candidate_source_sha256':owner.sha(candidate.encode()),'dependencies_sha256':{str(p.relative_to(owner.ROOT)):owner.sha(p.read_bytes()) for p in (Path(__file__),Path(owner.__file__),Path(campaign.__file__),Path(__file__).with_name('colorkey_rgb_hsv_candidate_20261001.py'),owner.HARNESS,BASE)},'cases':rows,'claims_not_made':['Temporary candidate; no production change','Native and controlled reference paths remain distinct','No all settings/geometry/threshold or native Windows UCRT/AE completion']}
    head=dict(r);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in rows)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==r
if __name__=='__main__':main()
