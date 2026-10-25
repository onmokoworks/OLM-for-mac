#!/usr/bin/env python3
"""Compile production handler bodies with real SDK recording suites; compare U03 rows."""
import argparse, gzip, hashlib, json, os, re, struct, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
MAIN=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
# KiraKira's UPDATE handler (UpdateRampUI) is compared against the original by mac/OLMKiraKira/tests/ui_compare.py (KiraKira-update session).
PLUGINS={'ColorKeep':('ColorKeep','SetColorsEnabled',True), 'ColorKey':('OLMColorKey','UpdateParameterUI',True), 'Blur':('OLMBlur','UpdateParamsUI',False), 'DirectionalBlur':('OLMDirectionalBlur','UpdateParamsUI',False), 'DistanceGradation':('OLMDistanceGradation','UpdateParamsUI',False), 'RadialBlur':('OLMRadialBlur','UpdateParamsUI',True), 'Smoother2':('OLMSmoother2','UpdateParamsUI',True),'KiraKira':('OLMKiraKira',None,False),'Smoother':('OLMSmoother',None,False),'ToonDilate':('OLMToonDilate',None,False)}
def function(source,name):
    m=re.search(r'static PF_Err\s+'+name+r'\(',source); assert m,name
    start=m.start(); i=source.index('{',m.end()); level=1; j=i+1
    while level:
        level+=(source[j]=='{')-(source[j]=='}'); j+=1
    return source[start:j]+'\n'
def scalar(p):
    b=bytes((p.get('value') or {}).get('bytes',[]))
    if not b:return 0
    return struct.unpack('<d',b)[0] if p['type']==10 else int.from_bytes(b[:4],'little',signed=True)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--scratch',type=Path,required=True); ap.add_argument('--witnesses',type=Path,default=HERE/'witnesses'); args=ap.parse_args()
    scratch=args.scratch.resolve(); scratch.mkdir(parents=True,exist_ok=True)
    manifest_path=args.witnesses/'manifest.json'
    if manifest_path.exists():
        for entry in json.loads(manifest_path.read_text())['sessions']:
            name=entry['name']
            assert hashlib.sha256((args.witnesses/(name+'.jsonl.gz')).read_bytes()).hexdigest()==entry['compressed_sha256']
            for i,digest in enumerate(entry['request_sha256']):
                assert hashlib.sha256((args.witnesses/(name+f'.batch{i}.request.json')).read_bytes()).hexdigest()==digest
    env={**os.environ,'TMPDIR':str(scratch)}; summary=[]
    for label,(plugin,handler,params) in PLUGINS.items():
        source=ROOT/'mac'/plugin/(plugin+'.cpp')
        if label=='Smoother2': source=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
        if label=='Smoother': source=ROOT/'mac/OLMSmoother/Mac/OLMSmoother_port.cpp'
        if label=='KiraKira': continue  # covered by mac/OLMKiraKira/tests/ui_compare.py
        if handler is None and not (args.witnesses/(label+'-update.jsonl.gz')).exists():continue
        text=source.read_text()
        body=f'#include "{ROOT/"mac"/plugin/(plugin+".h")}"\n#include "{ROOT}/mac/DynamicControls.h"\n'
        if label=='ColorKey': body+='template<class T> T ClampValue(T v,T lo,T hi) { return v<lo?lo:v>hi?hi:v; }\n'
        if label=='DirectionalBlur':body+='#include "AEFX_SuiteHandlerTemplate.h"\nstatic AEGP_PluginID g_aegp_plugin_id=0;\n#define OLM_DIRECTIONAL_REFUSAL(x) PF_Err_INTERNAL_STRUCT_DAMAGED\n'
        if label=='DistanceGradation':body+=function(text,'UpdateParamEnabled')
        if handler is None:
            assert 'case PF_Cmd_UPDATE_PARAMS_UI:' not in text
            assert 'case PF_Cmd_USER_CHANGED_PARAM:' not in text
            body+='#define INVOKE_UI PF_Err_NONE\n'
        else:
            assert 'case PF_Cmd_UPDATE_PARAMS_UI:' in text
            body+=function(text,handler)
            body+=f'#define INVOKE_UI {handler}(&in'+(',params' if params else '')+')\n'
        body+=f'#include "{HERE}/mac_host.cpp"\n'
        cpp=scratch/(label+'.cpp'); cpp.write_text(body); binary=scratch/label
        cmd=['clang++','-std=c++17','-O2','-Wno-deprecated-declarations','-Wno-pragma-pack',*[s for d in ['Headers','Headers/SP','Util','Resources'] for s in ['-I',str(MAIN/d)]],str(cpp),str(MAIN/'Util/AEGP_SuiteHandler.cpp'),str(MAIN/'Util/MissingSuiteError.cpp'),'-framework','Cocoa','-o',str(binary)]
        with (scratch/(label+'.build.log')).open('w') as log: subprocess.run(cmd,env=env,stdout=log,stderr=log,check=True)
        with gzip.open(args.witnesses/(label+'-update.jsonl.gz'),'rt') as f: rows=[json.loads(l)['event'] for l in f]
        cases=[]
        for row in rows:
            assert row['selector_error']==0
            assert [p['name_bytes'] for p in row['before']]==[p['name_bytes'] for p in row['after']]
            # Existing-state update and reload from values with fresh setup UI state.
            for reload in [False,True]:
                initial=[dict(p) for p in row['before']]
                if reload:
                    for p,default in zip(initial,rows[0]['before']):p['hidden']=default['hidden'];p['ui_flags']=default['ui_flags']
                cases.append((initial,row['after'],row['calls']))
        inputs=''.join(str(len(before))+'\n'+''.join(f"{p['type']} {p['ui_flags']} {int(p['hidden'])} {scalar(p)}\n" for p in before) for before,_,_ in cases)
        run=subprocess.run([str(binary)],input=inputs,text=True,capture_output=True,env=env,check=True)
        (scratch/(label+'.trace')).write_text(run.stdout)
        chunks=run.stdout.split('END\n');assert len(chunks)==len(cases)+1
        for idx,((before,after,calls),chunk) in enumerate(zip(cases,chunks)):
            mutations=[line for line in chunk.splitlines() if line.startswith(('H ','D '))]
            expected_calls=[f"H {c['slot']} {int(c['value'])}" if c['call']=='AEGP_SetDynamicStreamFlag' else f"D {c['slot']} {c['ui_flags']}" for c in calls]
            assert mutations==expected_calls,(label,idx,'ordered UI mutations differ')
            states=[list(map(int,line.split()[1:])) for line in chunk.splitlines() if line.startswith('S ')]
            expected=[[i,p['ui_flags'],int(p['hidden'])] for i,p in enumerate(after,1)]
            assert states==expected,(label,idx,next((a,b) for a,b in zip(states,expected) if a!=b))
        summary.append({'plugin':label,'updates':len(rows),'checks_including_reload':len(cases),'mismatches':0})
        print(json.dumps(summary[-1]),flush=True)
        binary.unlink()
    (scratch/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
