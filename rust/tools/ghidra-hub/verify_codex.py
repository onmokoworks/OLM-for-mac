"""One real codex exec run, isolated from unrelated user-configured MCP servers."""
import json
from pathlib import Path
import subprocess
import time
import psutil
from runtime import HOME, atomic_json

CODEX = Path('C:/Users/optim/AppData/Roaming/npm/node_modules/@openai/codex/node_modules/'
             '@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe')
PROMPT = '''Use only the olmghidra MCP server for this read-only smoke test. Do not use
shell, web, other MCPs, subagents, or edit any file. Call list_functions separately
for programs ["OLMBlur"] and ["OLMRadialBlur"], limit=2. Then call decompile_batch
once with four items: the two returned functions from each program. Use their
address strings as function selectors. Report program names, total function counts,
batch size, completed count, and the four function names. Do not return the C bodies.
You must actually make the MCP calls. If unavailable, report that failure.'''


def main():
    work = HOME/'codex-smoke'
    work.mkdir(exist_ok=True)
    args = [str(CODEX), 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
            '-C', str(work), '--sandbox', 'read-only', '--json',
            '-c', 'mcp_servers.olmghidra.url="http://127.0.0.1:8766/mcp"',
            '-c', 'mcp_servers.olmghidra.tool_timeout_sec=180',
            '-c', 'mcp_servers.olmghidra.default_tools_approval_mode="writes"',
            '-c', 'mcp_servers.olmghidra.enabled_tools=["list_functions","decompile_batch"]',
            '-o', str(HOME/'reports/codex-smoke.txt'), PROMPT]
    started = time.perf_counter()
    with (HOME/'logs/codex-smoke.jsonl').open('w', encoding='utf-8') as out, \
         (HOME/'logs/codex-smoke.stderr.log').open('w', encoding='utf-8') as err:
        process = subprocess.Popen(args, stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        owned = psutil.Process(process.pid)
        try:
            code = process.wait(timeout=300)
        except BaseException:
            members = owned.children(recursive=True)+[owned]
            for p in members:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs(members, timeout=10)
            if alive:
                raise RuntimeError(f'Codex helpers still alive: {[p.pid for p in alive]}')
            raise
    events = [json.loads(line) for line in (HOME/'logs/codex-smoke.jsonl').read_text(encoding='utf-8').splitlines()
              if line.startswith('{')]
    calls = [event['item'] for event in events if event.get('type') == 'item.completed'
             and event.get('item', {}).get('type') == 'mcp_tool_call']
    successful = [call for call in calls if call.get('status') == 'completed' and not call.get('error')]
    report = dict(pid=process.pid, exit_code=code, exited=not owned.is_running(),
                  seconds=time.perf_counter()-started,
                  mcp_list_evidence=sum(call['tool'] == 'list_functions' for call in successful) == 2,
                  mcp_batch_evidence=sum(call['tool'] == 'decompile_batch' for call in successful) == 1,
                  calls=[dict(tool=c['tool'], arguments=c['arguments'], status=c['status'], error=c.get('error')) for c in calls],
                  output=(HOME/'reports/codex-smoke.txt').read_text(encoding='utf-8')
                  if (HOME/'reports/codex-smoke.txt').exists() else '')
    atomic_json(HOME/'reports/codex-smoke.json', report)
    print(json.dumps(report), flush=True)
    assert code == 0 and report['mcp_list_evidence'] and report['mcp_batch_evidence']


if __name__ == '__main__':
    main()
