"""Capture pre-F01 retained bytes; run from repository root, TMPDIR in scratch."""
import importlib.util
import subprocess
import tarfile
from pathlib import Path

ROOT = Path.cwd()
STATE = ROOT / 'orchestra/state/G01-gate-after-cleanup/capture'
BASE = 'db59044515791af9890d0768c1fa4c7f5ad34034'
STATE.mkdir(parents=True, exist_ok=True)
archive = STATE / 'source.tar'
with archive.open('wb') as out:
    subprocess.run(['git', 'archive', BASE, 'mac/OLMDirectionalBlur', 'mac/DynamicControls.h', 'core', 'ucrtmath/include'], stdout=out, check=True)
with tarfile.open(archive) as source:
    source.extractall(STATE, filter='data')
spec = importlib.util.spec_from_file_location('probe', ROOT / 'tools/emulation/test_dblur_generic_backonly_beta_20260821.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
# Use the unchanged historical probe as the capture driver.
old = subprocess.check_output(['git', 'show', BASE + ':tools/emulation/test_dblur_generic_backonly_beta_20260821.py'], text=True)
import ast
module = ast.parse(old)
probe.CPP = next(ast.literal_eval(n.value) for n in module.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CPP' for t in n.targets))
probe.PRODUCTION = STATE / 'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'
needle = '    storage.clear_output();\n    storage.input_world.rowbytes = -1;'
probe.CPP = probe.CPP.replace(needle, '''    for (int y = 0; y < storage.height; ++y)
      std::fwrite(storage.output.data() + (std::size_t)y * storage.output_rowbytes,
                  sizeof(Pixel), storage.width, stdout);
''' + needle)
probe.CPP = probe.CPP[:probe.CPP.index('int main(int argc')] + '''int main() {
  if (retained_depth<PF_Pixel8>(8)) return 1;
  if (retained_depth<PF_Pixel16>(16)) return 2;
  if (retained_depth<PF_PixelFloat>(32)) return 3;
  return 0;
}
'''
for name in ('Headers', 'Resources', 'Util'):
    link = STATE / name
    if not link.exists():
        link.symlink_to(ROOT / name)
probe.ROOT = STATE
binary = probe.build(STATE, False)
with (STATE / 'retained.argb').open('wb') as out:
    subprocess.run([str(binary)], stdout=out, check=True)
print(STATE / 'retained.argb')
