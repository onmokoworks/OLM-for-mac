"""Verify saved task-owned harness exits without stopping any process.

Only the named validation directories are inspected. PID reuse is distinguished
by creation time and image path; workers' exit codes come from host diagnostics.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import subprocess


def live_process(pid):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
    kernel.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4
    kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        return {'state': 'absent' if error == 87 else 'query_denied', 'winerror': error}
    try:
        code = w.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            return {'state': 'query_failed', 'winerror': ctypes.get_last_error()}
        if code.value != 259:
            return {'state': 'exited', 'exit_code': code.value}
        times = [w.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
            return {'state': 'query_failed', 'winerror': ctypes.get_last_error()}
        created = ((times[0].dwHighDateTime << 32) + times[0].dwLowDateTime) / 1e7 - 11644473600
        buf = ctypes.create_unicode_buffer(32768)
        size = w.DWORD(len(buf))
        if not kernel.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return {'state': 'query_failed', 'winerror': ctypes.get_last_error()}
        return {'state': 'running', 'image': buf.value, 'created_unix': created}
    finally:
        kernel.CloseHandle(handle)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('directories', type=Path, nargs='+')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    records = []
    for root in args.directories:
        for path in sorted(root.glob('**/*.process.json')):
            data = json.loads(path.read_text())
            worker = json.loads(data['stdout']).get('worker_diagnostics', {})
            record = {'log': str(path.resolve()), 'pid': data['pid'],
                      'expected_image': data['argv'][0],
                      'returncode': data['returncode'], 'worker_exit_code': worker.get('exit_code'),
                      'worker_classification': worker.get('classification'),
                      'completed_log_unix': path.stat().st_mtime}
            live = live_process(data['pid'])
            record['pid_query'] = live
            record['verified_exited'] = live['state'] in ['absent', 'exited']
            if live['state'] == 'running':
                record['pid_reused'] = (live['created_unix'] > path.stat().st_mtime
                    or Path(live['image']).resolve() != Path(data['argv'][0]).resolve())
                record['verified_exited'] = record['pid_reused']
            records.append(record)
    denied = sorted({r['pid'] for r in records if r['pid_query']['state'] == 'query_denied'})
    if denied:
        # Protected processes can reuse an exited harness PID. Query just those
        # IDs through CIM; never infer ownership from a process name alone.
        filt = ' OR '.join(f'ProcessId = {int(pid)}' for pid in denied)
        command = (f"Get-CimInstance Win32_Process -Filter '{filt}' | "
                   "Select-Object ProcessId,Name,@{Name='CreatedUnix';Expression={"
                   "([DateTimeOffset]$_.CreationDate).ToUnixTimeMilliseconds()/1000}} | "
                   "ConvertTo-Json -Compress")
        raw = subprocess.check_output(['powershell', '-NoProfile', '-Command', command], text=True)
        cim = json.loads(raw) if raw.strip() else []
        if isinstance(cim, dict): cim = [cim]
        by_pid = {r['ProcessId']: r for r in cim}
        for record in records:
            if record['pid'] not in denied: continue
            followup = by_pid.get(record['pid'])
            record['pid_query_followup'] = followup
            record['verified_exited'] = followup is None or (
                followup['CreatedUnix'] > record['completed_log_unix']
                and followup['Name'].lower() != Path(record['expected_image']).name.lower())
    result = {'records': records, 'count': len(records),
              'all_harness_exits_verified': bool(records) and all(r['verified_exited'] for r in records),
              'all_recorded_exit_codes_zero': bool(records) and all(r['returncode'] == 0 for r in records),
              'worker_exit_counts': {str(k): sum(r['worker_exit_code'] == k for r in records)
                                     for k in set(r['worker_exit_code'] for r in records)}}
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}, indent=2))
