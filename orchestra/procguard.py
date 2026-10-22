#!/usr/bin/env python3
"""Process-explosion guard for orchestra workers (16 GB Mac).

Every INTERVAL seconds: count Python processes and swap use. If either crosses its
threshold, snapshot the full process table, find the orchestra worker whose
process-group subtree is largest, kill that whole group, and log what happened.
Also reaps orphaned Codex MCP helpers (PPID 1, matching MCP_PATTERNS) older than 10 min.
"""
import os, re, signal, subprocess, sys, time
from pathlib import Path

MAIN = Path("/Users/onmk/Documents/Projects/Personal/OLM as")
STATE = MAIN / "orchestra/state"
MAX_PY = int(os.environ.get("PROCGUARD_MAX_PY", "150"))
MAX_SWAP_MB = int(os.environ.get("PROCGUARD_MAX_SWAP_MB", "8192"))
INTERVAL = int(os.environ.get("PROCGUARD_INTERVAL", "5"))
MCP_PATTERNS = ("strands-agents-sops mcp", "3d-mcp-4-5-8", "/mcp/", "ghidra")


def table():
    out = subprocess.run(["ps", "-axo", "pid=,ppid=,pgid=,stat=,etime=,rss=,command="],
                         capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split(None, 6)
        if len(parts) == 7 and not parts[3].startswith("Z"):  # ignore zombies
            pid, ppid, pgid, st, et, rss, cmd = parts
            rows.append(dict(pid=int(pid), ppid=int(ppid), pgid=int(pgid), etime=et, rss=int(rss), cmd=cmd))
    return rows


def swap_mb():
    s = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout
    m = re.search(r"used = ([\d.]+)M", s)
    return float(m.group(1)) if m else 0.0


def etime_s(et):
    d, _, rest = et.rpartition("-")
    parts = [int(p) for p in rest.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return int(d or 0) * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]


def log(msg):
    with open(STATE / "procguard.log", "a") as f:
        f.write(time.strftime("%F %T ") + msg + "\n")


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    log(f"start max_py={MAX_PY} max_swap_mb={MAX_SWAP_MB}")
    while True:
        rows = table()
        py = [r for r in rows if "Python" in r["cmd"] or re.search(r"\bpython3?\b", r["cmd"])]
        sw = swap_mb()
        # reap orphaned MCP helpers left by finished Codex sessions
        for r in rows:
            if r["ppid"] == 1 and any(p in r["cmd"] for p in MCP_PATTERNS) and etime_s(r["etime"]) > 600:
                try:
                    os.kill(r["pid"], signal.SIGTERM); log(f"reaped orphan MCP {r['pid']} {r['cmd'][:120]}")
                except ProcessLookupError:
                    pass
        if len(py) > MAX_PY or sw > MAX_SWAP_MB:
            snap = STATE / f"procguard-{time.strftime('%Y%m%d-%H%M%S')}.txt"
            snap.write_text("\n".join(f"{r['pid']} {r['ppid']} {r['pgid']} {r['etime']} {r['rss']} {r['cmd']}" for r in rows))
            groups = {}
            for r in rows:
                groups.setdefault(r["pgid"], []).append(r)
            # worker groups are led by run.sh sessions (command mentions orchestra/run.sh or a worktree path)
            cand = [(len(g), pg, g) for pg, g in groups.items()
                    if any("orchestra/run.sh" in r["cmd"] or "/worktrees/" in r["cmd"] for r in g) and pg > 1]
            cand.sort(reverse=True)
            if cand:
                n, pg, g = cand[0]
                leader = next((r for r in g if "orchestra/run.sh" in r["cmd"]), g[0])
                log(f"TRIP py={len(py)} swap={sw:.0f}MB -> killpg {pg} ({n} procs) leader={leader['cmd'][:160]} snapshot={snap.name}")
                # stop the owning worker too (Codex runs each command in its own group, and would retry)
                ids = sorted({m.group(1) for r in g for m in [re.search(r"/worktrees/([^/ ]+)", r["cmd"])] if m})
                for wid in ids:
                    subprocess.run(["pkill", "-TERM", "-f", f"run.sh {wid}"])
                    subprocess.run(["pkill", "-TERM", "-f", f"worktrees/{wid}"])
                    log(f"stopped worker {wid}")
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    for r in g:
                        try:
                            os.kill(r["pid"], sig)
                        except (ProcessLookupError, PermissionError):
                            pass
                    try:
                        os.killpg(pg, sig)
                    except (ProcessLookupError, PermissionError):
                        pass
                    time.sleep(3)
                for wid in ids:
                    subprocess.run(["pkill", "-KILL", "-f", f"worktrees/{wid}"])
            else:
                log(f"TRIP py={len(py)} swap={sw:.0f}MB but no worker group found; snapshot={snap.name}")
            time.sleep(30)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
