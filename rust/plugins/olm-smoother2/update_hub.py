"""Isolate the shared hub implementation without editing shared tool sources."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'tools/ghidra-hub'))
import runtime
runtime.HOME = HERE / 'upstream-work/hub'
runtime.HOME.mkdir(parents=True, exist_ok=True)
runtime.start_jvm.__defaults__ = (runtime.HOME,)
runtime.open_project.__defaults__ = (runtime.HOME,)
import hub
hub.__file__ = __file__  # Child must apply the same private-home override.
if __name__ == '__main__':
    hub.main()
