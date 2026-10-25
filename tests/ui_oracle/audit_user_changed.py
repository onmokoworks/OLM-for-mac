#!/usr/bin/env python3
"""Static selector13 audit; explicitly not a U03 execution witness."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ENTRIES={'ColorKeep':'1800025c0','OLMBlur':'18000a970','OLMDirectionalBlur':'1800083f0','DistanceGradation':'181174bd0','OLMSmoother':'18000a2c0'}
LEAVES={'OLMColorKey':'18000b660','OLMKiraKira':'1811517e0','OLMRadialBlur':'18000bc00','OLMSmoother2':'1800056f0','OLMToonDilate':'1801a7300'}
def read(plugin,address):
    return subprocess.check_output(['python3',str(ROOT/'orchestra/reports/U01-read-function.py'),plugin,address],text=True)
def main():
    inventory={r['plugin']:r for r in json.loads((ROOT/'orchestra/reports/U01-ui-inventory.json').read_text())};rows=[]
    for plugin in [*ENTRIES,*LEAVES]:
        entry=read(plugin,ENTRIES.get(plugin,'entry_point'));assert entry
        if plugin in LEAVES:
            leaf=read(plugin,LEAVES[plugin]);assert re.search(r'\{\s*return;\s*\}',leaf)
            assert inventory[plugin]['effect_vtables'][0][6]=='0x'+LEAVES[plugin]
            branch=entry.split('case 0xd:',1)[1].split('break;',1)[0];assert '+ 0x28' in branch
            kind='empty virtual USER_CHANGED method'
        elif plugin=='ColorKeep':
            leaf='';branch=entry.split('case 0xd:',1)[1].split('break;',1)[0]
            assert 'FUN_180002210' in branch and 'FUN_180002210' in entry.split('case 0xe:',1)[1].split('break;',1)[0]
            kind='same function as UPDATE_PARAMS_UI'
        else:
            leaf='';assert 'case 0xd:' not in entry;kind='no selector13 case'
        mac_plugin='OLMDistanceGradation' if plugin=='DistanceGradation' else plugin
        source=ROOT/'mac'/mac_plugin/(mac_plugin+'.cpp')
        if plugin=='OLMSmoother':source=ROOT/'mac/OLMSmoother/Mac/OLMSmoother_port.cpp'
        if plugin=='OLMSmoother2':source=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
        mac=source.read_text()
        if plugin=='ColorKeep':
            assert re.search(r'case PF_Cmd_USER_CHANGED_PARAM:\s*err = SetColorsEnabled\(in_data, params\); break;',mac)
        elif plugin=='OLMRadialBlur':
            branch=mac.split('case PF_Cmd_USER_CHANGED_PARAM:',1)[1].split('break;',1)[0]
            branch=re.sub(r'//[^\n]*','',branch).replace('case PF_Cmd_EVENT:','');assert not branch.strip()
        else:assert 'case PF_Cmd_USER_CHANGED_PARAM:' not in mac
        rows.append({'plugin':plugin,'original_sha256':inventory[plugin]['sha256'],'static_dispatch':kind,'entry':ENTRIES.get(plugin,'entry_point'),'leaf':LEAVES.get(plugin),'decomp_excerpt_sha256':hashlib.sha256((entry+leaf).encode()).hexdigest(),'mac_dispatch_agrees':True})
    print(json.dumps({'mode':'static_not_execution','plugins':rows},indent=2))
if __name__=='__main__':main()
