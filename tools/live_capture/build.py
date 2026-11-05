#!/usr/bin/env python3
"""Release-equivalent builds using SDK paths without creating root-level links."""
import json, os, re, subprocess
from pathlib import Path
from targets import T23, TICKET, PLUGINS
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state'/TICKET
SDK=Path.home()/'Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples'
STATE.mkdir(parents=True,exist_ok=True)
(STATE/'tmp').mkdir(exist_ok=True)
for plugin in PLUGINS:
    source=ROOT/'mac'/plugin/'Mac'
    project=STATE/(plugin+'.xcodeproj');project.mkdir(exist_ok=True)
    body=(source/(plugin+'.xcodeproj/project.pbxproj')).read_text()
    for directory in ('Headers','Util','Resources'):
        body=re.sub(r'(?<![\w"/])\.\./\.\./\.\./'+directory+r'(/[\w.]+)*',lambda m:json.dumps(str(SDK/m.group()[9:])),body)
    body=re.sub(r'path = (\.\./[^;]+);',lambda m:'path = '+json.dumps(str((source/m.group(1)).resolve()))+';',body)
    body=body.replace('$(SRCROOT)',str(source)).replace('INFOPLIST_FILE = Info.plist;', 'INFOPLIST_FILE = '+json.dumps(str(source/'Info.plist'))+';')
    (project/'project.pbxproj').write_text(body)
    command=['xcodebuild','-project',str(project),'-configuration','Debug','-jobs','1',f'SRCROOT={source}',f'SOURCE_ROOT={source}',
        'HEADER_SEARCH_PATHS='+ ' '.join(chr(34)+str(SDK/d)+chr(34) for d in ('Headers','Headers/SP','Util','Resources'))+' '+chr(34)+str(ROOT/'core')+chr(34),
        f'INFOPLIST_FILE={source}/{plugin}.plugin-Info.plist',
        'ARCHS=arm64 x86_64','ONLY_ACTIVE_ARCH=NO','MACOSX_DEPLOYMENT_TARGET=11.0',
        f'OBJROOT={STATE}/obj/{plugin}',f'SHARED_PRECOMPS_DIR={STATE}/precompiled/{plugin}',f'CONFIGURATION_BUILD_DIR={STATE}/build',
        'GCC_OPTIMIZATION_LEVEL='+('2' if plugin=='OLMDistanceGradation' else '3'),
        'DEBUG_INFORMATION_FORMAT=dwarf-with-dsym','ENABLE_TESTABILITY=NO','COPY_PHASE_STRIP=YES','build']
    (STATE/(plugin+'-build-command.json')).write_text(json.dumps(command,indent=2))
    with (STATE/('build-'+plugin+'.log')).open('w') as log:
        subprocess.run(command,env=dict(os.environ,TMPDIR=str(STATE/'tmp')),stdout=log,stderr=subprocess.STDOUT,check=True)
    print(plugin,'built',flush=True)
