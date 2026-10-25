"""Compile the real arbitrary callbacks; feed the 34 valid original PE table records."""
import os
from pathlib import Path
import subprocess
import pefile
root=Path(__file__).resolve().parents[3]
main=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
scratch=root/'orchestra/state/U02-kirakira-ramp-editor/persistence'
scratch.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(scratch))
plugin=root/'mac/OLMKiraKira'
host=(root/'tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp').read_text().split('template <class Pixel> static void set_pixel',1)[0]
host=f'#define KIRA_SOURCE "{plugin}/OLMKiraKira.cpp"\n#define KIRA_STRINGS_SOURCE "{plugin}/OLMKiraKira_Strings.cpp"\n'+host
host+=(plugin/'tests/persistence.cpp').read_text()
(scratch/'host.cpp').write_text(host)
sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True,env=env).strip()
command=['clang++','-std=c++17','-O2','-ffp-contract=off','-fno-fast-math','-Wno-deprecated-declarations','-Wno-pragma-pack','-isysroot',sdk,
         *[x for p in ('Headers','Headers/SP','Util','Resources') for x in ('-I',str(main/p))],
         str(scratch/'host.cpp'),str(main/'Util/AEGP_SuiteHandler.cpp'),str(main/'Util/MissingSuiteError.cpp'),
         '-framework','Cocoa','-o',str(scratch/'persistence')]
with (scratch/'build.log').open('w') as log:
    subprocess.run(['sh',str(root/'ucrtmath/build.sh'),str(scratch/'ucrtmath')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(command+[str(scratch/'ucrtmath/libucrtmath.a')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
pe=pefile.PE(str(main/'plugins_2025/OLMKiraKira.aex'))
payload=pe.get_data(0x1814d7030-pe.OPTIONAL_HEADER.ImageBase,34*0x144)
subprocess.run([str(scratch/'persistence')],input=payload,env=env,check=True)
