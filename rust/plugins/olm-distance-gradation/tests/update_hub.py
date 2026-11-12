"""Job-local hub root override; shared tool sources remain read-only."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/ghidra-hub'))
import runtime

runtime.HOME = Path(__file__).resolve().parents[1] / 'validation/upstream/hub'
runtime.HOME.mkdir(parents=True, exist_ok=True)
runtime.start_jvm.__defaults__ = (runtime.HOME,)
runtime.open_project.__defaults__ = (runtime.HOME,)
if __name__ == '__main__':
    if sys.argv[1] == 'serve':
        from server import serve
        serve(int(sys.argv[2]), sys.argv[3], 2)
    elif sys.argv[1] == 'stop':
        import hub
        print(hub.stop())
