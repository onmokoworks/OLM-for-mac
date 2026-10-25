"""Compile a Classic-only in-process MFR test; timing requires the shared lock."""
import subprocess,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P07c-smoother-threading';D=S/('concurrent-tsan' if '--tsan' in sys.argv else 'concurrent');D.mkdir(exist_ok=True)
body=(R/'tools/emulation/olmsmoother_v1_public_guard_harness_20260812.cpp').read_text().split('static unsigned short Widen',1)[0]
body=body.replace('../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp',str(R/'mac/OLMSmoother/Mac/OLMSmoother_port.cpp'))
test=(R/'orchestra/reports/P07c-evidence/concurrent.cpp').read_text()
if '--tsan' in sys.argv:test=test.replace('repeat<5','repeat<1').replace('1920,1080','512,512')
(D/'host.cpp').write_text(body+test)
env=dict(os.environ,TMPDIR=str(D),TMP=str(D),TEMP=str(D))
cmd=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I'+str(R/'cli/OLMSmoother/shim'),str(D/'host.cpp'),'-o',str(D/'host')]
if '--tsan' in sys.argv:cmd += ['-fsanitize=thread','-g'];env['TSAN_OPTIONS']='halt_on_error=1'
subprocess.run(cmd,env=env,check=True)
subprocess.run(['lockf','-k',str(Path.home()/'.cache/olm-emu/bench.lock'),str(D/'host')],env=env,check=True)
