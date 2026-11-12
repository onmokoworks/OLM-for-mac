"""Sequential, bounded profile campaign for the ten supplied originals."""
import argparse
import subprocess
from pathlib import Path
import olm_triage as t

NAMES = ("ColorKeep", "DistanceGradation", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
         "OLMKiraKira", "OLMRadialBlur", "OLMSmoother", "OLMSmoother2", "OLMToonDilate")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--originals", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--analysis-timeout", type=int, default=900)
    p.add_argument("--names", default=",".join(NAMES), help="comma-separated subset for a bounded retry")
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    statuses = []
    names = a.names.split(",")
    if any(n not in NAMES for n in names):
        p.error("--names must be a subset of the ten originals")
    for name in names:
        argv = ["profile", "--aex", str(a.originals / (name + ".aex")), "--out", str(a.out / name),
                "--cache", str(t.HERE / "local" / "ghidra-cache"), "--analysis-timeout", str(a.analysis_timeout),
                "--size", "17x9", "--jobs", "1"]
        try:
            status = {"name": name, "exit_code": t.main(argv)}
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            status = {"name": name, "exit_code": 2, "error": str(exc)}
        statuses.append(status)
        t.oracle.write_json(a.out / "index.json", statuses)
        print(status, flush=True)
    raise SystemExit(2 if any(s["exit_code"] for s in statuses) else 0)
