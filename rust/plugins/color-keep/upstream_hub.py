"""Run the shared hub in this job's private project; never touch the shared hub."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parents[1] / "tools" / "ghidra-hub"))
import runtime

runtime.HOME = HERE / "validation" / "upstream-20261112" / "hub"
runtime.HOME.mkdir(parents=True, exist_ok=True)
runtime.start_jvm.__defaults__ = (runtime.HOME,)
runtime.open_project.__defaults__ = (runtime.HOME,)
import hub

hub.__file__ = __file__
if __name__ == "__main__":
    hub.main()
