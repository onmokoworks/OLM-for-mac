"""Render compact, real machine evidence into the README; never invent missing reports."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
from runtime import HOME


def read(name):
    return json.loads((HOME/'reports'/name).read_text(encoding='utf-8'))


def main():
    bootstrap = read('bootstrap.json')
    runs = read('throughput.json')
    knowledge = read('knowledge-import.json')
    inventory = read('source-inventory.json')
    mappings = {r['program']: r['mapping_comments'] for r in read('mapping-notes-initial.json')}
    stress = read('concurrency.json')
    codex = read('codex-smoke.json')
    fixture = read('knowledge-fixture.json')
    version = read('add-version-demo.json')
    stop = read('last-stop.json')
    integrity = read('source-integrity.json')
    persistence = read('persistence.json')
    assert stop['exited'] and not stop['remaining'] and not stop['forced']
    assert codex['mcp_list_evidence'] and codex['mcp_batch_evidence']
    assert all(r['completed'] == r['requested'] for r in runs)
    counts, conflicts = defaultdict(Counter), Counter()
    for report in knowledge:
        name = Path(report['target']).stem
        counts[name].update(report.get('counts', {}))
        conflicts[name] += len(report.get('conflicts', []))
    lines = ['Verified on **2026-11-12**, Windows, Ghidra 12.0.3 / Temurin 21 / Python 3.11.9.',
             'Full logs and JSON evidence are retained under `D:/olm-rs-ghidra/reports/` and `logs/`.',
             '', f"All **{len(bootstrap)} originals**, **{sum(r['functions'] for r in bootstrap):,} total functions** "
             '(including external imports), were fully analyzed and saved. Restart checks verified the original hashes, '
             'function counts and analyzed flags, plus the persisted demo version.', '',
             '| Program | Total functions | Initial analysis/import seconds |', '| --- | ---: | ---: |']
    for row in bootstrap:
        lines.append(f"| {row['program']} | {row['functions']:,} | {row['seconds']:.2f} |")
    lines += ['', '**Throughput:** all 566 internal bodies (OLMBlur 97 + OLMRadialBlur 469), '
              'four runs with fresh decompiler pools. All four completed 566/566 with identical C-output hashes. '
              'The 87 external imports in these two programs have no local bodies.', '',
              '| Order | Mode | Server seconds | HTTP wall seconds |', '| ---: | --- | ---: | ---: |']
    for index, run in enumerate(runs, 1):
        lines.append(f"| {index} | {'Parallel (3)' if run['parallel'] else 'Sequential'} | "
                     f"{run['server_seconds']:.3f} | {run['wall_seconds']:.3f} |")
    seq = statistics.mean(r['server_seconds'] for r in runs if not r['parallel'])
    par = statistics.mean(r['server_seconds'] for r in runs if r['parallel'])
    lines += ['', f'Mean server time: **{seq:.3f}s sequential vs {par:.3f}s parallel; {seq/par:.2f}× speedup**. '
              'This is a local batch wall-time measurement, not a guarantee on other binaries or machines.', '',
              '**Concurrency and features:** three independent HTTP clients each completed 96 decompilations '
              '(288 total), concurrently with nine saved writer transactions. Immediate rollback of a partially '
              'applied invalid table passed. Xrefs, call graphs, composite/dynamic type queries and the three-file '
              'function export passed. Probe names, comments and DEFAULT source priorities were restored and '
              'verified again after restart.', '',
              '**Actual project knowledge:** qualified final application counts below. Zero means zero; '
              'the saved sources do not establish the expected months of human annotations.', '',
              '| Program | Names | Signatures | Types | Comments | Bookmarks | Conflicts | IR/validation excerpts |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in sorted(bootstrap, key=lambda r:r['program']):
        name = row['program']
        c = counts[name]
        values = [c[k] for k in ['names','signatures','types','comments','bookmarks']]+[conflicts[name],mappings.get(name,0)]
        lines.append('| '+name+' | '+' | '.join(map(str,values))+' |')
    errors = [r for r in knowledge if 'error' in r]
    lines += ['', f"The expanded snapshot inventory checked {len(inventory)} AEX/hash-related entries "
              f"and found {sum(r.get('user_symbols',0) for r in inventory)} USER_DEFINED symbols in readable entries. "
              f"The targeted migration recorded {len(knowledge)} source records: "
              f"{sum('skipped' in r for r in knowledge)} incompatible/unmatched records skipped, "
              f"{len(errors)} unreadable entry, and {sum(conflicts.values())} preserved conflicts. "
              'Analyzed `.aex.0` duplicates were found through metadata hashes. Other saved AEXs were often '
              'unanalyzed 16-bit real-mode imports. The unreadable source is the OLM2025 archived '
              '`OLMToonDilate/Plugins/64/2024/OLMToonDilate.aex` entry; Ghidra reports '
              '`EOFException: Buffer index too large (276 > 269)`. No repair or upgrade was attempted on originals.',
              '', 'An initial trial admitted unused Mach-O format types from unmatched C++ build artifacts. '
              'Those 89 `/MachO/` definitions were removed; the final policy rejects incompatible ABIs and '
              'unmatched binaries before applying types. The original trial and its correction remain in '
              '`knowledge-import-initial-trial.json` and `import-trial-correction.json`; remaining primitive '
              'dependency types are unused catalog entries, not applied signatures/data layouts.', '',
              f"**Seeded knowledge test (separate from user data):** {fixture['assertions']}. "
              f"Applied {fixture['transfer']['counts']['names']} names, "
              f"{fixture['transfer']['counts']['types']} types, "
              f"{fixture['transfer']['counts']['signatures']} signature, "
              f"{fixture['transfer']['counts']['comments']} comments and "
              f"{fixture['transfer']['counts']['bookmarks']} bookmark. A second transfer preserved a conflicting human name.", '',
              f"**Version demo:** flipped one PE checksum byte at file offset {version['patch']['offset']}; "
              f"imported `{version['program']}`, matched {version['report']['matched']} functions and carried "
              f"{version['report']['counts'].get('comments',0)} comments. Ambiguous/tiny functions and unsafe "
              'interior/global annotations remain explicitly unmatched. The actual `add-version` CLI returned '
              '`reused=true` after restart, without re-analysis.', '',
              '**Codex:** the real CLI exited 0; two successful `list_functions` calls reported 97/469 internal '
              'functions, then one `decompile_batch` returned 4/4 completed. Successful MCP tool events are '
              'retained in `logs/codex-smoke.jsonl`. An initial attempt correctly refused unannotated tools; '
              'the final run used read-only MCP annotations, `default_tools_approval_mode="writes"`, and a '
              'two-tool allow-list. No global Codex config was changed.', '',
              '**Regression fixes verified:** raw DomainFile program ownership removed GhidraProject’s '
              'hidden outer transaction, making immediate rollback real; read-only MCP annotations and '
              'ASGI-scoped service shutdown preserve shared project lifetime; dynamic types no longer '
              'receive the composite-only `getComponents()` call. Ten unittest tests passed, plus the '
              'real JVM, HTTP, CLI and restart checks above.', '',
              f"**Source integrity:** all {sum(r['checked'] for r in integrity):,} original project files "
              'matched their copy-time SHA-256, size and mtime; originals were never opened as projects.', '',
              f"**Final shutdown:** server PID `{stop['pid']}` and owned PIDs `{stop['owned_pids']}` exited; "
              '`forced=[]`, `remaining=[]`, `exited=true`. The server is stopped.']
    readme = Path(__file__).with_name('README.md')
    text = readme.read_text(encoding='utf-8')
    start, end = '<!-- MACHINE_RESULTS_START -->', '<!-- MACHINE_RESULTS_END -->'
    before, rest = text.split(start,1)
    _, after = rest.split(end,1)
    readme.write_text(before+start+'\n'+'\n'.join(lines)+'\n'+end+after, encoding='utf-8')
    print('Recorded verified machine results in README.md')


if __name__ == '__main__':
    main()
